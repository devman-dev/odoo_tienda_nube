from odoo import _, api, fields, models

class ProductImage(models.Model):
    _name = 'product.image.tn'
    _description = "Product Image Tienda Nube"
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(default=10)

    image_1920 = fields.Image()

    product_tmpl_tn_id = fields.Many2one(
        string="Product Template", comodel_name='product.template', ondelete='cascade', index=True,
    )