"""Sales Pipeline business logic — all state-mutation rules live here."""

from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, require_deal_ownership, require_team_scope
from app.models.deal import Deal, DealStage
from app.repositories.activity_repository import ActivityRepository
from app.repositories.deal_repository import DealRepository
from app.schemas.deal import DealCreate, DealUpdate
from app.schemas.forecast import (
    ClosedWonTotal,
    ForecastPeriod,
    ForecastResponse,
    StageTotal,
)

_SYSTEM_ACTOR_ID = 0


class DealService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = DealRepository(db)
        self._activity = ActivityRepository(db)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(self, payload: DealCreate, current_user: CurrentUser) -> Deal:
        from app.models.contact import Account  # noqa: PLC0415

        account = await self._db.get(Account, payload.account_id)
        if account is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Account not found")

        # Sales Reps may only create deals for themselves
        if current_user.role == "Sales Rep" and payload.owner_id != current_user.id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Sales Reps can only create deals assigned to themselves.",
            )

        seq = await self._repo.get_next_seq()
        deal = Deal(
            ref_id=f"DEAL-{seq:04d}",
            title=payload.title,
            value=payload.value,
            stage=payload.stage,
            expected_close_date=payload.expected_close_date,
            owner_id=payload.owner_id,
            account_id=payload.account_id,
            contact_id=payload.contact_id,
        )
        deal = await self._repo.create(deal)

        await self._activity.insert_log(
            deal_id=deal.id,
            action_type="deal_created",
            actor_id=current_user.id,
        )

        # Notify owner when a different user creates and assigns the deal
        if payload.owner_id != current_user.id:
            await self._dispatch_notification(
                user_id=payload.owner_id,
                message=f"Deal {deal.ref_id} was assigned to you",
                entity_id=deal.id,
            )

        await self._db.flush()
        return deal

    # ------------------------------------------------------------------
    # Update editable fields
    # ------------------------------------------------------------------

    async def update(self, deal: Deal, payload: DealUpdate, current_user: CurrentUser) -> Deal:
        require_deal_ownership(deal.owner_id, current_user)

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return deal

        if "account_id" in updates and updates["account_id"] is not None:
            from app.models.contact import Account  # noqa: PLC0415
            account = await self._db.get(Account, updates["account_id"])
            if account is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Account not found")

        for field in updates:
            await self._activity.insert_log(
                deal_id=deal.id,
                action_type="field_updated",
                actor_id=current_user.id,
                note=f"{field} updated",
            )

        deal = await self._repo.update(deal, **updates)
        return deal

    # ------------------------------------------------------------------
    # Stage transition
    # ------------------------------------------------------------------

    async def change_stage(
        self,
        deal: Deal,
        new_stage: DealStage,
        loss_reason: str | None,
        current_user: CurrentUser,
    ) -> Deal:
        require_deal_ownership(deal.owner_id, current_user)

        if deal.stage.is_terminal:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"detail": "Deal is already in a terminal stage", "code": "TERMINAL_STAGE"},
            )

        if new_stage == DealStage.CLOSED_LOST and not (loss_reason or "").strip():
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"detail": "loss_reason is required for Closed Lost", "code": "LOSS_REASON_REQUIRED"},
            )

        previous_stage = deal.stage
        fields: dict = {"stage": new_stage}

        if loss_reason:
            fields["loss_reason"] = loss_reason

        # Clear is_overdue atomically on any closed transition
        if new_stage.is_terminal:
            fields["is_overdue"] = False

        deal = await self._repo.update(deal, **fields)
        await self._activity.insert_log(
            deal_id=deal.id,
            action_type="stage_changed",
            actor_id=current_user.id,
            note=f"{previous_stage.value} → {new_stage.value}",
        )
        await self._db.flush()
        return deal

    # ------------------------------------------------------------------
    # Forecast
    # ------------------------------------------------------------------

    async def get_forecast(
        self, period_start: date, period_end: date
    ) -> ForecastResponse:
        rows = await self._repo.forecast_aggregate(period_start, period_end)
        row_map: dict[DealStage, tuple[int, Decimal]] = {
            row[0]: (row[1], row[2]) for row in rows
        }

        open_stages = [
            DealStage.LEAD_IN,
            DealStage.QUALIFIED,
            DealStage.PROPOSAL,
            DealStage.NEGOTIATION,
        ]
        open_pipeline: list[StageTotal] = []
        total_weighted = Decimal("0.00")

        for stage in open_stages:
            count, total_val = row_map.get(stage, (0, Decimal("0.00")))
            prob = DealStage.probability(stage)
            weighted = (total_val * prob).quantize(Decimal("0.01"))
            total_weighted += weighted
            open_pipeline.append(
                StageTotal(
                    stage=stage,
                    deal_count=count,
                    total_value=total_val.quantize(Decimal("0.01")),
                    probability=float(prob),
                    weighted_value=weighted,
                )
            )

        cw_count, cw_value = row_map.get(DealStage.CLOSED_WON, (0, Decimal("0.00")))

        return ForecastResponse(
            period=ForecastPeriod(start=period_start, end=period_end),
            open_pipeline=open_pipeline,
            closed_won=ClosedWonTotal(
                deal_count=cw_count,
                total_value=cw_value.quantize(Decimal("0.01")),
            ),
            total_weighted_forecast=total_weighted,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _dispatch_notification(
        self, *, user_id: int, message: str, entity_id: int | None = None
    ) -> None:
        from app.models.base import Notification  # noqa: PLC0415
        self._db.add(
            Notification(
                user_id=user_id,
                message=message,
                entity_type="deal",
                entity_id=entity_id,
            )
        )
