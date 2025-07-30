#import Odoo and Python libraries
from odoo.exceptions import UserError
from odoo import models, fields, api, _
import requests
import logging

_logger = logging.getLogger(__name__)  # Standard Odoo logging

# --- Log model to track sync results and alerts ---
class WarehouseSyncLog(models.Model):
    _name = "warehouse.sync.log"
    _description = "Warehouse Sync Alerts"
    
    user_id = fields.Many2one('res.users', string='Triggered By', readonly=True)
    status = fields.Selection([
        ('success', 'Success'),
        ('failure', 'Failure'),
    ], string='Status', readonly=True)
    message = fields.Text(string='Message', readonly=True)

    # Basic info for log record
    main_id = fields.Char("External ID")        # External system's item number
    sku = fields.Char("SKU")                    # Stock Keeping Unit code
    barcode = fields.Char("Barcode")            # Barcode (unique identifier)
    quantity = fields.Float("Quantity")         # Synced Odoo quantity
    alert = fields.Boolean("Alert (onhand < 5)")# True if low stock after sync
    note = fields.Text("Note")                  # Message about this sync event


# --- Add computed field to product.template for latest synced warehouse qty ---
class ProductTemplate(models.Model):
    _inherit = "product.template"

    main_warehouse_qty = fields.Float("Main Warehouse Quantity",
                                      compute="_compute_main_qty",
                                      store=True)

    @api.depends("default_code", "barcode")
    def _compute_main_qty(self):
        for product in self:
            # Look up latest sync log for this product (by SKU or barcode)
            sync = self.env["warehouse.sync.log"].search(
                ["|", ("sku", "=", product.default_code), ("barcode", "=", product.barcode)],
                limit=1, order="id desc"
            )
            product.main_warehouse_qty = sync.quantity if sync else 0.0


# --- Main Sync Utility ---
class WarehouseSync(models.Model):
    _name = "warehouse.sync"
    _description = "Warehouse Stock Sync Utility"
    
    @api.model
    def run_sync(self):    
        """
        This method is the entry point for running the sync.
        It calls sync_products(), and logs the result (success/fail and message).
        """
        try:
            self.sync_products()  # Actually run the sync
        
            message = "Sync successful"
            status = 'success'
        except Exception as e:
            message = f"Sync failed: {str(e)}"
            status = 'fail'
        
        # Log the overall sync result
        self.env['warehouse.sync.log'].create({
            'user_id': self.env.uid,
            'status': status,
            'message': message,
        })
        # Send sync report
        self._send_sync_report()
    
    def sync_products(self):
        """
        This method calls the external API, processes each product,
        updates Odoo stock and publishes/unpublishes products based on alert status.
        """
        url = "https://connect.oskarme.com/api/v1/product/product-details?getAll=true"
        try:
            response = requests.get(url)       # Call the external API
            payload = response.json()          # Parse the response JSON

            if not payload.get("success") or "data" not in payload:
                _logger.error("Invalid response from API: %s", payload)
                return

            # Loop through each product returned by API
            for item in payload["data"]:
                sku = item.get("sku")
                ext_id = item.get("itemNumber")
                barcode = str(item.get("barcode"))
                qty = float(item.get("southbayStock") or 0.0)

                # Find matching product in Odoo by SKU or barcode
                product = None
                if sku:
                    product = self.env["product.product"].search([("default_code", "=", sku)], limit=1)
                if not product and barcode:
                    product = self.env["product.product"].search([("barcode", "=", barcode)], limit=1)
                if not product:
                    continue  # Skip if product not found

                # Apply stock rules (mapping warehouse qty to Odoo qty)
                if qty == 0:
                    new_qty = 0
                elif 30 <= qty <= 50:
                    new_qty = 2
                elif qty < 30:
                    new_qty = 0
                elif 50 < qty < 200:
                    new_qty = 5
                elif qty >= 200:
                    new_qty = 10
                else:
                    new_qty = product.qty_available  # fallback to current Odoo stock if unmatched

                odoo_qty = product.qty_available
                alert = new_qty < 5  # Flag for low stock alert

                # Log the sync result for this product
                self.env["warehouse.sync.log"].create({
                    "sku": sku,
                    "main_id": ext_id,
                    "barcode": barcode,
                    "quantity": new_qty,
                    "alert": alert,
                    "note": (
                        "LOW STOCK — DISABLED SALE" if alert else
                        f"Stock rule triggered: new Odoo qty = {new_qty}" if new_qty != odoo_qty else
                        "Stock OK"
                    )
                })

                # Only update Odoo if stock changed
                if new_qty != odoo_qty:
                    location = self.env.ref("stock.stock_location_stock")
                    quant = self.env['stock.quant'].sudo().search([
                        ('product_id', '=', product.id),
                        ('location_id', '=', location.id)
                    ], limit=1)

                    if quant:
                        quant.sudo().quantity = new_qty  # Update qty
                    else:
                        self.env['stock.quant'].sudo().create({
                            'product_id': product.id,
                            'location_id': location.id,
                            'quantity': new_qty
                        })

                # Unpublish product on website if alert (low stock), publish otherwise
                product.product_tmpl_id.website_published = not alert

            _logger.info("✅ Warehouse sync completed successfully.")

        except Exception as e:
            _logger.exception("Error syncing warehouse: %s", str(e))
            
    def _send_sync_report(self):
        """
        Send a report of the sync results to the configured email address.
        """
        log = self.env['warehouse.sync.log']
        log = log.search([], order = 'create_date desc', limit=100)
        
        total = len(log)
        low = sum(1 for l in log if l.alert)
        
        # post summery in the current user's inbox
        summery = (
            f"Warehouse Sync Report\n"
            f"- Total Products Synced: {total}\n"
            f"- Products with Low Stock (onhand < 5): {low}\n"
        )

        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title' : "Warehouse Sync Report",
                'body' : summery,
                'sticky' : True,
                'type' : 'info',
                'timeout' : 20000,
                # 'button' : [
                #     {
                #         'name' : 'View Report',
                #         'type' : 'object',
                #         'class' : 'btn-primary',
                #         'action' : 'action_view_report',
                #     }
                # ],
            }
        )
        
        # post summary in the current user's inbox
        user = self.env.user
        user_partner = user.partner_id
        
        # Create a proper inbox notification using message_post
        user_partner.message_post(
            body=summery,
            subject='Warehouse Sync Report',
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
            partner_ids=[user_partner.id]
        )
        
        try:
            user.notify_info(summery, title="Warehouse Sync Report")
        except Exception:
            pass
        
        # prepare details HTML table for email
        rows = "".join([
            "<tr>"
            f"<td>{l.create_date.strftime('%Y-%m-%d %H:%M:%S')}</td>"
            f"<td>{l.sku or 'N/A'}</td>"
            f"<td>{l.barcode or 'N/A'}</td>"
            f"<td>{l.main_id or 'N/A'}</td>"
            f"<td>{l.quantity or 'N/A'}</td>"
            f"<td>{'Yes' if l.alert else 'No'}</td>"
            f"<td>{l.note or 'N/A'}</td>"
            "</tr>"
            for l in log
            ])
        
        body_html = f"""
            <p>Dear Manager</p>
            <p>Warehouse Sync Report</p>
            <table border="1" cellpadding="5" cellspacing="0">
                <thead>
                    <tr>
                        <th>Create Date</th>
                        <th>SKU</th>
                        <th>Barcode</th>
                        <th>Main ID</th>
                        <th>Quantity</th>
                        <th>Alert</th>
                        <th>Note</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <p>Best Regards</p>
            <p>Warehouse Sync Utility</p>
        """
        
        # send email
        cfg = self.env['warehouse.sync.config'].search([], limit=1)
        if not cfg or not cfg.report_email:
            _logger.warning("No report email configured. Skipping email.")
            return
        
        mail_values = {
            'subject' : "Warehouse Sync Report",
            'body_html' : body_html,
            'email_to' : cfg.report_email,
            'email_from' : self.env.user.email or 'darkness.boogeyman85@gmail.com',
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        
