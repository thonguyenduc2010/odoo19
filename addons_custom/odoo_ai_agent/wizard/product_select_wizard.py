import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields

class ProductQuantityWizard(models.TransientModel):
    _name = 'product.quantity.wizard'
    _description = 'Product Quantity Wizard'
    agent_id = fields.Many2one('copilot.agent.dashboard', string='Agent')
    line_ids = fields.One2many('product.quantity.wizard.line','wizard_id', string="Products")

    def action_confirm(self):
        list_of_product = []
        for wizard in self:
            for line in wizard.line_ids:
                product = line.product_id
                quantity = line.quantity
                for vendor in product.seller_ids:
                    list_of_product.append({
                        'product_id': product.id,
                        'product_name': product.display_name,
                        'vendor_id': vendor.partner_id.id,
                        'vendor_name': vendor.partner_id.name,
                        'product_qty': quantity,
                        'price_unit': vendor.price,
                    })
        if list_of_product:
            new_record = self.agent_id
            new_record.with_context(with_data_line_product=list_of_product).run_agent()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': ' Successfully Finished Running',
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'message': ' Please add product and Run',
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }



class ProductQuantityWizardLine(models.TransientModel):
    _name = 'product.quantity.wizard.line'
    _description = 'Product Quantity Wizard Line'

    wizard_id = fields.Many2one('product.quantity.wizard', string="Wizard")
    product_id = fields.Many2one('product.product', string="Product", required=True,  domain="[('type', 'in', ['product']),('purchase_ok', '=', True)]")
    quantity = fields.Float(string="Quantity", required=True, default=1.0)