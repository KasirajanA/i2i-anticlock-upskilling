from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.security import CurrentUser, get_current_user
from app.permissions import MODULE_PERMISSIONS, MODULE_WRITE_PERMISSIONS


def require_module_access(module: str, write: bool = False) -> Callable:
    """FastAPI dependency factory: enforce module-level role access.

    Args:
        module: Key in MODULE_PERMISSIONS / MODULE_WRITE_PERMISSIONS.
        write: When True, use the stricter write permission set.
    """

    async def _dependency(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        allowed = MODULE_WRITE_PERMISSIONS[module] if write else MODULE_PERMISSIONS[module]
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )
        return current_user

    return _dependency
