"""Module-level permission matrix — single source of truth.

Each key is a module slug. Values are tuples of roles that may READ the module.
MODULE_WRITE_PERMISSIONS restricts mutations to a tighter set where applicable.
"""

MODULE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "contacts": ("Admin", "Manager", "Sales Rep", "Support Agent"),
    "sales_pipeline": ("Admin", "Manager", "Sales Rep"),
    "contracts": ("Admin", "Manager", "Sales Rep"),
    "customer_support": ("Admin", "Manager", "Support Agent"),
    "analytics": ("Admin", "Manager", "Sales Rep", "Support Agent"),
    "user_team_management": ("Admin",),
}

MODULE_WRITE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "contacts": ("Admin", "Manager", "Sales Rep"),
    "sales_pipeline": ("Admin", "Manager", "Sales Rep"),
    "contracts": ("Admin", "Manager", "Sales Rep"),
    "customer_support": ("Admin", "Manager", "Support Agent"),
    "analytics": ("Admin", "Manager"),
    "user_team_management": ("Admin",),
}
