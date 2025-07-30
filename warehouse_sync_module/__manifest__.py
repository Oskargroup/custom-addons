{
    "name": "Warehouse Sync",
    "version": "1.6",
    "description": "Syncs main warehouse data with Odoo Inventory",
    "author": "Abolfazl Rezaei",
    "category": "Inventory",
    "depends": ["stock", "website_sale"],
    "data": [
        "data/cron.xml",
        "views/warehouse_sync_log_views.xml",
        "views/warehouse_sync_config_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
}
