import logging
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class TiendaNubeProductProductInherit(models.Model):
    _inherit = "product.product"

    product_id_tn = fields.Char('ID Tienda Nube', help="ID Variante Tienda Nube", copy=False)
    stock_ilimitado_tn = fields.Boolean('Stock Ilimitado en Tienda Nube', help="Stock Ilimitado en Tienda Nube")
    precio_promocional_tn = fields.Float('Precio Promocional Tienda Nube', help="Precio promocional de Tienda Nube")

    #Dimensiones TN
    alto_tn = fields.Float('Alto en CM', help="Alto en Tienda Nube")
    ancho_tn = fields.Float('Ancho en CM', help="Ancho en Tienda Nube")
    profundidad_tn = fields.Float('Profundidad en CM', help="Profundidad en Tienda Nube")
    peso_tn = fields.Float('Peso en Kg', help="Peso en Tienda Nube")

    #Instagram y Google Shopping
    mpn_tn = fields.Char('MPN', help="MPN (Número de pieza del fabricante) en Tienda Nube")
    rango_edad_tn = fields.Selection([
        ('newborn', '0-3 Meses'),
        ('infant', '3-12 Meses'),
        ('toddler', '1-5 Años'),
        ('kids', '5-13 Años'),
        ('adult', 'Adulto'),
    ], string='Rango de Edad', help="Rango de Edad en Tienda Nube")
    sexo_tn = fields.Selection([
        ('unisex', 'Unisex'),
        ('male', 'Masculino'),
        ('female', 'Femenino'),
    ], string='Sexo', help="Sexo en Tienda Nube", default='unisex')

    # Sobreescribimos unlink para que no se pueda borrar producto de descuento y envio de Tienda Nube
    def unlink(self):
        product_discount_tn = self.env.ref('odoo_tienda_nube.product_discount_tn')
        product_shipping_tn = self.env.ref('odoo_tienda_nube.product_shipping_tn')
        for product in self:
            if product.id == product_discount_tn.id:
                raise ValidationError(_("No se puede borrar el producto de descuento de Tienda Nube"))
            if product.id == product_shipping_tn.id:
                raise ValidationError(_("No se puede borrar el producto de envío de Tienda Nube"))
        return super(TiendaNubeProductProductInherit, self).unlink()
