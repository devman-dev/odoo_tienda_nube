from odoo.exceptions import ValidationError

from odoo import models, fields, api

class MassSynchronizeProductsWizard(models.TransientModel):
    _name = 'mass.synchronize.products.wizard'
    _description = 'Wizard to synchronize products with Tienda Nube'

    synchronize_products_ids = fields.One2many('mass.synchronize.products.wizard.line', 'wizard_id', 'Productos')
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company)

    def set_id_tn(self):
        for product in self.synchronize_products_ids:
            if product.tn_id:
                # Si el template del product.product tiene mas variantes asignamos product_id_tn, en el caso de que sea una sola variante asignamos id_tn
                if product.product_id.product_tmpl_id.product_variant_count > 1:
                    product.product_id.product_id_tn = product.variant_tn_id
                    # Asignamos el id_tn al templatate si no tiene ya uno asignado entendiendo que es el mismo para todas las variantes
                    if not product.product_id.product_tmpl_id.id_tn:
                        product.product_id.product_tmpl_id.id_tn = product.tn_id
                else:
                    product.product_id.product_id_tn = product.variant_tn_id
                    product.product_id.product_tmpl_id.id_tn = product.tn_id

    def get_products_barcode_tn(self):
        self.synchronize_products_ids = False
        #Obtenemos todos los productos de tienda nube
        #Primero creamos todas las categorias en Odoo
        self.company_id.get_all_categories_tn()
        products = self.company_id.get_all_products_tn()

        if products:
            lines = []
            for product in products:
                if 'variants' in product and product['variants']:
                    for variant in product['variants']:
                        if not variant.get('barcode'):
                            continue  # Skip variants without Barcode
                        product_tmp = self.env['product.product'].search([('barcode', '=', variant['barcode']), ('id_tn', '=', False),('product_id_tn', '=', False)], limit=1)
                        if product_tmp:
                            line = {
                                'product_id': product_tmp.id,
                                'tn_id': str(product['id']),
                                'variant_tn_id': str(variant['id']) if len(product['variants']) > 1 else str(product['id']),
                                'product_tn_name': product['name']['es'] + " SKU: " + variant['barcode'] if 'name' in product else '',
                            }
                            lines.append((0, 0, line))
            if not lines:
                raise ValidationError("No se encontraron productos con código de barras en Tienda Nube que no estén sincronizados con Odoo.")
            self.synchronize_products_ids = lines

        # Refrescamos el wizard para mostrar los productos obtenidos
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mass.synchronize.products.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('odoo_tienda_nube.view_mass_synchronize_products_wizard_form').id,
            'target': 'new',
            'res_id': self.id,
        }

    def get_products_sku_tn(self):
        self.synchronize_products_ids = False
        #Obtenemos todos los productos de tienda nube
        #Primero creamos todas las categorias en Odoo
        self.company_id.get_all_categories_tn()
        products = self.company_id.get_all_products_tn()

        if products:
            lines = []
            for product in products:
                if 'variants' in product and product['variants']:
                    for variant in product['variants']:
                        if not variant.get('sku'):
                            continue  # Skip variants without SKU
                        product_tmp = self.env['product.product'].search([('default_code', '=', variant['sku']), ('id_tn', '=', False),('product_id_tn', '=', False)], limit=1)
                        if product_tmp:
                            line = {
                                'product_id': product_tmp.id,
                                'tn_id': str(product['id']),
                                'variant_tn_id': str(variant['id']),
                                'product_tn_name': product['name']['es'] + " SKU: " + variant['sku'] if 'name' in product else '',
                            }
                            lines.append((0, 0, line))
            if not lines:
                raise ValidationError("No se encontraron productos con referencia interna (SKU) en Tienda Nube que no estén sincronizados con Odoo.")
            self.synchronize_products_ids = lines

        # Refrescamos el wizard para mostrar los productos obtenidos
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mass.synchronize.products.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('odoo_tienda_nube.view_mass_synchronize_products_wizard_form').id,
            'target': 'new',
            'res_id': self.id,
        }



class MassSynchronizeProductsWizardLine(models.TransientModel):
    _name = 'mass.synchronize.products.wizard.line'

    wizard_id = fields.Many2one('mass.synchronize.products.wizard', 'Wizard')
    product_id = fields.Many2one('product.product', 'Producto')
    barcode = fields.Char('Código de Barras', help="Código de Barras del Producto", related='product_id.barcode')
    tn_id = fields.Char('ID de Producto en Tienda Nube', help="ID de Producto en Tienda Nube")
    variant_tn_id = fields.Char('ID de Variante en Tienda Nube', help="ID de Variante en Tienda Nube")
    product_tn_name = fields.Char('Producto en Tienda Nube', readonly=True)