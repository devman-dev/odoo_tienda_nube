import logging
import requests
import base64
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class TiendaNubeProductTemplateInherit(models.Model):
    _inherit = "product.template"

    id_tn = fields.Char('ID Tienda Nube', help="ID de Tienda Nube", copy=False)
    envio_gratis_tn = fields.Boolean('Envio Gratis Tienda Nube', help="Indica si el producto tiene envio gratis en Tienda Nube")
    mostrar_en_tienda_tn = fields.Boolean('Mostrar en Tienda Nube', help="Indica si el producto se mostrará en Tienda Nube")
    categoria_tn_ids = fields.Many2many('category.tn', string='Categorias Tienda Nube', help="Categorias de Tienda Nube")

    # Sobreescribimos unlink para que no se pueda borrar producto de descuento de Tienda Nube
    def unlink(self):
        product_discount_tn = self.env.ref('tiendanube_odoo.product_discount_tn_product_template')
        for product in self:
            if product.id == product_discount_tn.id:
                raise ValidationError(_("No se puede borrar el producto de descuento de Tienda Nube"))
        return super(TiendaNubeProductProductInherit, self).unlink()

    # Metodo de actualizacion desde Odoo a TN
    def update_tn(self):
        for product in self:
            if product.id_tn:
                self.env.user.company_id.update_product_tn(product)

    # Metodo de actualizacion de stock desde Odoo a TN
    def update_stock_tn(self):
        for product in self:
            if product.id_tn:
                self.env.user.company_id.update_product_stock_tn(product)

    # Metodo para crear el producto en TN
    def create_tn(self):
        for product in self:
            if not product.id_tn:
                self.env.user.company_id.create_product_tn(product)

    # Metodo para crear/actualizar producto en Odoo desde TN por medio de id GET /products/{id}
    def create_update_product_from_tn(self):

        company = self.env.user.company_id
        # Primero creamos todas las categorias en Odoo por si tenemos alguna faltante
        company.get_all_categories_tn()

        # Creamos el producto
        headers = company.get_headers_tn()
        url = "https://api.tiendanube.com/v1/%s/products/%s" % (company.tiendanube_id, self.id_tn)
        

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            product = response.json()

            categoria_tn_ids = []
            for category in product['categories']:
                category_odoo = self.env['category.tn'].search([('tn_id', '=', category['id'])])
                categoria_tn_ids.append(category_odoo.id)

            #Asignamos la primer imagen al producto
            #Buscamos imagen la cual se encuentra en list images con el id que tenemos en variant['image_id']
            if product['images']:
                url_imagen = product['images'][0]['src']
            else:
                url_imagen = False
            image_template_base64 = False
            if url_imagen:
                response = requests.get(url_imagen)
                if response.status_code == 200:
                    image_template_base64 = base64.b64encode(response.content)
                    
            _logger.info("Data: %s", product)
            self.name = product['name']['es']
            self.description_sale = product['description']['es']
            self.id_tn = product['id']
            self.envio_gratis_tn = product['free_shipping']
            self.mostrar_en_tienda_tn = product['published']
            self.categoria_tn_ids = [(6, 0, categoria_tn_ids)]
            self.image_1920 = image_template_base64
            self.detailed_type = 'product' if product['requires_shipping'] else 'service'
            
            #Verificamos si tiene atributos y de ser asi creamos los faltantes, asi como cada una de las variables de esos atributos
            if product['attributes']:

                index = 0 # Flag para recorrer los valores de las variantes ya que vinen ordenados segun el orden de los atributos
                for attribute in product['attributes']:
                    _logger.info("Attribute: %s", attribute)
                    #Buscamos si existe el atributo
                    attribute_odoo = self.env['product.attribute'].search([('name', '=', attribute['es'])])
                    if not attribute_odoo:
                        #Creamos atributo
                        attribute_odoo = self.env['product.attribute'].create({
                            'name': attribute['es'],
                            'create_variant': 'always'
                        })
                    ids_vales = []
                    for variant in product['variants']:

                        value_attribute_odoo = self.env['product.attribute.value'].search([('name', '=', variant['values'][index]['es']),('attribute_id', '=', attribute_odoo.id)])
                        if not value_attribute_odoo:
                            #Creamos valor
                            value_attribute_odoo = self.env['product.attribute.value'].create({
                                'name': variant['values'][index]['es'],
                                'attribute_id': attribute_odoo.id,
                            })
                        ids_vales.append(value_attribute_odoo.id)

                    index += 1
                    #Agregamos al product.template el atributo y variantes del mismo
                    #Verificamos si ya existe el atributo en el product.template
                    if not self.attribute_line_ids.filtered(lambda x: x.attribute_id.id == attribute_odoo.id):
                        self.write({
                            'attribute_line_ids': [(0, 0, {
                                'attribute_id': attribute_odoo.id,
                                'value_ids': [(6, 0, ids_vales)],
                            })]
                        })
                    else:
                        #Si existe el atributo, verificamos si existen los valores
                        attribute_line = self.attribute_line_ids.filtered(lambda x: x.attribute_id.id == attribute_odoo.id)
                        for value_id in ids_vales:
                            if not attribute_line.value_ids.filtered(lambda x: x.id == value_id):
                                attribute_line.write({
                                    'value_ids': [(4, value_id)]
                                })
            #Recorremos variantes
            for variant in product['variants']:
                _logger.info("Variant: %s", variant)

                #Creo una lista para lugo usarla para buscar el product.product que tenga los atributos y valores guardados
                atributos = []
                index = 0
                for value in variant['values']:
                    atributos.append({
                        'atributo':product['attributes'][index]['es'], #Nombre del atributo
                        'valor':value['es'],
                    })
                    index += 1

                #Filtro de self.product_variant_ids el product.product que tenga los mismo atraibutos y valores
                product_variant_odoo = False
                for product_variant in self.product_variant_ids:
                    atributos_variant = []
                    for value in product_variant.product_template_attribute_value_ids:
                        atributos_variant.append({
                            'atributo':value.attribute_id.name, #Nombre del atributo
                            'valor':value.name,
                        })
                    if atributos == atributos_variant:
                        product_variant_odoo = product_variant
                        break

                if product_variant_odoo:
                    #Buscamos imagen la cual se encuentra en list images con el id que tenemos en variant['image_id']
                    url_imagen = False
                    for image in product['images']:
                        if image['id'] == variant['image_id']:
                            url_imagen = image['src']
                            break
                    #Obtenida la url converitmos la imagen a base64 y guardamos
                    if url_imagen:
                        _logger.info("URL Imagen: %s", url_imagen)
                        response = requests.get(url_imagen)
                        if response.status_code == 200:
                            image_base64 = base64.b64encode(response.content)
                            product_variant_odoo.image_1920 = image_base64
                

                    #Verificamos si podemos usar el barcode
                    
                    product_barcode_exist = self.env['product.product'].sudo().search([('barcode', '=', variant['barcode'])])
                    
                    product_variant_odoo.sudo().write({
                        'product_id_tn': variant['id'],
                        'list_price': float(variant['price']) if variant['price'] else 0,
                        #'standard_price': float(variant['cost']) if variant['cost'] else 0, TODO al estar relacionado con Almacen el costo da error de permisos al actualizar
                        'precio_promocional_tn': float(variant['promotional_price']) if variant['promotional_price'] else 0,
                        'alto_tn': float(variant['height']),
                        'ancho_tn': float(variant['width']),
                        'profundidad_tn': float(variant['depth']),
                        'peso_tn': float(variant['weight']),
                        'mpn_tn': variant['mpn'],
                        'rango_edad_tn': variant['age_group'],
                        'sexo_tn': variant['gender'],
                        'barcode': variant['barcode'] if not product_barcode_exist else False,
                        'default_code': variant['sku'],
                        'inventory_level_id_tn': variant['inventory_levels'][0]['id'],
                        'location_id_tn': variant['inventory_levels'][0]['location_id'],
                    })
            _logger.info("********** Finalizacion de creacion: %s", self.name)



        else:
            _logger.info("Error: %s", response.text)
            raise ValidationError(_("Error al crear el producto"))

