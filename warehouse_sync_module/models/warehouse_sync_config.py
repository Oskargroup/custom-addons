from odoo import models, fields

class WarehouseSyncConfig(models.Model):
    _name = "warehouse.sync.config"
    _description = "Warehouse Sync Configuration"
    
    report_email = fields.Char(
        string = "Report Email",
        default = "darkness.boogeyman85@gmail.com",
    )    
    
