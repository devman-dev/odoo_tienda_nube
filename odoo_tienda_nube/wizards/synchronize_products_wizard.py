import logging

from odoo import models, fields, api
_logger = logging.getLogger('GetTnLocationWizard')

class SynchronizeProductsWizard(models.TransientModel):
    _name = 'synchronize.products.wizard'
    _description = 'Wizard to synchronize products with Tienda Nube'

    synchronize_products_ids = fields.One2many('synchronize.products.wizard.line', 'wizard_id', 'Productos')

    def set_id_tn(self):
        for product in self.synchronize_products_ids:
            if product.tn_id:
                product.product_id.id_tn = product.tn_id

class SynchronizeProductsWizardLine(models.TransientModel):
    _name = 'synchronize.products.wizard.line'

    wizard_id = fields.Many2one('synchronize.products.wizard', 'Wizard')
    product_id = fields.Many2one('product.template', 'Producto')
    tn_id = fields.Char('ID de Producto en Tienda Nube', help="ID de Producto en Tienda Nube")
