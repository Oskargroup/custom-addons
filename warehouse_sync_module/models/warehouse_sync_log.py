from odoo import models, fields, api
from odoo.exceptions import UserError

# This model stores every warehouse sync event and alert in Odoo
class WarehouseSyncLog(models.Model):
    _name = 'warehouse.sync.log'                # Odoo technical name for the model
    _description = 'Warehouse Sync Log'         # Display name in UI
    _order = 'create_date desc'                 # Default sort: newest logs first
      
    # --- BASIC FIELDS ---
    create_date = fields.Datetime('Date', readonly=True)   # When this log entry was created
    user_id = fields.Many2one('res.users', string='Triggered By', readonly=True)  # Who triggered the sync
    status = fields.Selection([
        ('success', 'Success'),
        ('fail', 'Fail')
    ], string='Status', readonly=True)        # Did the overall sync succeed or fail?
    message = fields.Text('Message', readonly=True)        # Details about the sync attempt
    
    # --- CUSTOM FIELDS FOR WAREHOUSE LOGIC ---
    sku = fields.Char('SKU')                                # Product SKU involved in this log entry
    main_id = fields.Char('External Main ID')               # External system's unique product ID
    barcode = fields.Char('Barcode')                        # Product barcode
    quantity = fields.Float('Quantity')                     # Stock quantity as synced
    alert = fields.Boolean('Alert (onhand < 5)')            # True if stock is low
    note = fields.Text('Note')                              # Message about stock state (e.g., 'LOW STOCK')

    # --- BUTTON: Allow user to trigger a manual sync from the UI ---
    @api.model
    def manual_sync(self):
        # Find a sync configuration (assumes only one config exists; adjust if needed)
        sync = self.env['warehouse.sync'].search([], limit=1)
        if not sync:
            # If no sync config found, show error to user
            raise UserError('No warehouse sync configuration found.')
        sync.run_sync()  # Trigger the sync process
        # Reload the page in the web UI so user sees updated logs/status
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
