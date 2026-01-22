import logging
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import requests
import base64
import random

_logger = logging.getLogger(__name__)

class TiendaNubeResCompanyInherit(models.Model):
    _inherit = "res.company"

    tiendanube_access_token = fields.Char('Tienda Nube Access Token', help="Token otorgado por Tienda Nube")
    tiendanube_id = fields.Char('Tienda Nube User ID', help="ID de Tienda Nube")
    tn_config_stock = fields.Selection([
        ('stock', 'Stock en mano'),
        ('stock-price', 'Stock pronosticado'),
    ], string='Configuracion de Stock', default='stock', help="Si es 'Stock en mano' se actualiza el stock en base a la cantidad en mano, si es 'Stock pronosticado' se actualiza el stock en base a la cantidad pronosticada")
    tn_config_confirmation_sale = fields.Boolean('Confirmar venta', help="Si esta activo se confirma la venta al crear la orden de venta, sino se deja en estado borrador")
    tn_config_stock_realtime = fields.Boolean('Stock en tiempo real', help="Si esta activo se actualiza el stock en tiempo real, sino se actualiza cada 30 minutos")
    tn_pricelist_id = fields.Many2one('product.pricelist', string='Lista de Precios Tienda Nube', help="Lista de precios que se usara para los productos de Tienda Nube", required=True)
    tn_config_update_product_price_cron = fields.Boolean('Actualizar precios cada X tiempo', help="Si esta activo se actualizan los precios de los productos en Tienda Nube automaticamente cada dia o segun temporalidad en el cron configurado")
    tn_type_tax = fields.Selection([
        ('included', 'Incluido'),
        ('not_included', 'No incluido'),
    ], string='Tipo de Impuesto Tienda Nube', default='included', help="Si es 'Incluido' el precio incluye el impuesto, si es 'No incluido' el precio no incluye el impuesto")

    # Conf sincronizacion de productos
    update_product_tn_name = fields.Boolean('Actualizar nombre', default=True, help="Si esta activo se actualiza el nombre del producto en Tienda Nube")
    update_product_tn_categories = fields.Boolean('Actualizar categorias', default=True, help="Si esta activo se actualizan las categorias del producto en Tienda Nube")
    update_product_tn_free_shipping = fields.Boolean('Actualizar Envio Gratis', default=True, help="Si esta activo se actualiza el envio gratis del producto en Tienda Nube")
    update_product_tn_promotional_price = fields.Boolean('Actualizar Precio Promocional', default=True, help="Si esta activo se actualiza el precio promocional en Tienda Nube")
    update_product_tn_dimensions = fields.Boolean('Actualizar Dimensiones', default=True, help="Si esta activo se actualizan las dimensiones del producto en Tienda Nube")
    update_product_tn_sku = fields.Boolean('Actualizar SKU', default=True, help="Si esta activo se actualiza el SKU del producto en Tienda Nube")
    update_product_tn_mpn = fields.Boolean('Actualizar MPN', default=True, help="Si esta activo se actualiza el MPN del producto en Tienda Nube")
    update_product_tn_age_group = fields.Boolean('Actualizar Rango de Edad', default=True, help="Si esta activo se actualiza el rango de edad del producto en Tienda Nube")
    update_product_tn_gender = fields.Boolean('Actualizar Sexo', default=True, help="Si esta activo se actualiza el sexo del producto en Tienda Nube")
    update_product_tn_cost = fields.Boolean('Actualizar Costo', default=True, help="Si esta activo se actualiza el costo del producto en Tienda Nube")
    update_product_tn_description = fields.Boolean('Actualizar Descripcion', default=True, help="Si esta activo se actualiza la descripcion del producto en Tienda Nube") 
    update_product_tn_published = fields.Boolean('Actualizar Publicacion', default=True, help="Si esta activo se actualiza la publicacion del producto en Tienda Nube")

    def update_product_images_tn(self, products):
        headers = self.get_headers_tn()
        for product in products:
            if not product.id_tn:
                continue
            url = "https://api.tiendanube.com/v1/%s/products/%s" % (self.tiendanube_id, product.id_tn)
            response_product = requests.get(url, headers=headers)
            if response_product.status_code == 200:
                data_products = response_product.json()
                for variant in data_products['variants']:
                    product_variant_odoo = product.product_variant_ids.filtered(lambda x: x.product_id_tn == str(variant['id']))
                    if product_variant_odoo:
                        #Reemplazamos imagen en TN por la actual - PUT /products/{product_id}/images/{id}
                        if product_variant_odoo.image_1920:
                            url_put_image = "https://api.tiendanube.com/v1/%s/products/%s/images/%s" % (self.tiendanube_id, product.id_tn, variant['image_id'])
                            response_image_variant = requests.put(url_put_image, headers=headers, json={
                                "src": self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/ati_tn_product_template_ids/' + str(product_variant_odoo.id),
                            })
                            # Si obtenemos un 404 es porque la imagen no existe, por lo que la creamos
                            if response_image_variant.status_code == 404:
                                url_post_image = "https://api.tiendanube.com/v1/%s/products/%s/images" % (self.tiendanube_id, product.id_tn)
                                response_post_image = requests.post(url_post_image, headers=headers, json={
                                    "src": self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/ati_tn_product_template_ids/' + str(product_variant_odoo.id),
                                })
                        # Si no se contemplan las variantes breake al ciclo para que solo cargue una imagen principal
                        if not product.contemplar_imagen_variantes_tn:
                            # Borramos todas las demas imagenes que no corresponden a la variante principal
                            for imagen in data_products['variants']:
                                if imagen['image_id'] != variant['image_id']:
                                    url_delete_image = "https://api.tiendanube.com/v1/%s/products/%s/images/%s" % (self.tiendanube_id, product.id_tn, imagen['image_id'])
                                    response_delete_image = requests.delete(url_delete_image, headers=headers)
                            break 
                # Recorremos ['images'] y eliminamos las que no corresponden a ninguna variante
                for image in data_products['images']:
                    existe = False
                    for variant in data_products['variants']:
                        if image['id'] == variant['image_id']:
                            existe = True
                            break
                    if not existe:
                        url_delete_image = "https://api.tiendanube.com/v1/%s/products/%s/images/%s" % (self.tiendanube_id, product.id_tn, image['id'])
                        response_delete_image = requests.delete(url_delete_image, headers=headers)
                        
                # Publicamos imagenes de galeria si existen
                for image in product.product_template_image_tn_ids:
                    url_post_image = "https://api.tiendanube.com/v1/%s/products/%s/images" % (self.tiendanube_id, product.id_tn)
                    response_post_image = requests.post(url_post_image, headers=headers, json={
                        "src": self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/ati_tn_product_template_galery_ids/' + str(image.id),
                    })

    def get_all_products_tn(self):

        # Tenemos en cuenta paginacion con 30 por pagina, por lo que obtenemos todos los productos hasta encontrarnos con un code 404
        headers = self.get_headers_tn()
        products = []
        for page in range(1, 1000):
            url = "https://api.tiendanube.com/v1/%s/products?page=%s&per_page=30" % (self.tiendanube_id, page)
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if page == 1:
                    products = data
                else:
                    products += data
            elif response.status_code == 404:
                break
            else:
                raise ValidationError('Error al obtener productos de Tienda Nube: %s' % response.text)
        return products

    def get_headers_tn(self):
        return {
            "Authentication": "bearer " + self.tiendanube_access_token,
            "Content-Type": "application/json",
            "User-Agent": "Odoo by Devoo"
        }

    #Creamos productos de TN en Odoo
    def create_products_in_odoo(self):
        #Primero creamos todas las categorias en Odoo
        self.get_all_categories_tn()
        products = self.get_all_products_tn()
        for product in products:
            #Verificamos si existe el product_template
            product_template_odoo = self.env['product.template'].search([('id_tn', '=', product['id'])])

            categoria_tn_ids = []
            for category in product['categories']:
                category_odoo = self.env['category.tn'].search([('tn_id', '=', category['id'])])
                categoria_tn_ids.append(category_odoo.id)

            if not product_template_odoo:

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

                #Creamos product_template
                product_template_odoo = self.env['product.template'].create({
                    'id_tn': product['id'],
                    'name': product['name']['es'],
                    'type': 'consu' if product['requires_shipping'] else 'service',
                    'is_storable': True if product['requires_shipping'] else False,
                    'envio_gratis_tn': product['free_shipping'],
                    'mostrar_en_tienda_tn': product['published'],
                    'image_1920': image_template_base64,
                    'categoria_tn_ids': [(6, 0, categoria_tn_ids)],
                    'description_sale': product['description']['es'],
                })

            #Verificamos si tiene atributos y de ser asi creamos los faltantes, asi como cada una de las variables de esos atributos
            if product['attributes']:

                index = 0 # Flag para recorrer los valores de las variantes ya que vinen ordenados segun el orden de los atributos
                for attribute in product['attributes']:
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
                    if not product_template_odoo.attribute_line_ids.filtered(lambda x: x.attribute_id.id == attribute_odoo.id):
                        product_template_odoo.write({
                            'attribute_line_ids': [(0, 0, {
                                'attribute_id': attribute_odoo.id,
                                'value_ids': [(6, 0, ids_vales)],
                            })]
                        })
                    else:
                        #Si existe el atributo, verificamos si existen los valores
                        attribute_line = product_template_odoo.attribute_line_ids.filtered(lambda x: x.attribute_id.id == attribute_odoo.id)
                        for value_id in ids_vales:
                            if not attribute_line.value_ids.filtered(lambda x: x.id == value_id):
                                attribute_line.write({
                                    'value_ids': [(4, value_id)]
                                })
            #Recorremos variantes
            for variant in product['variants']:

                #Creo una lista para lugo usarla para buscar el product.product que tenga los atributos y valores guardados
                atributos = []
                index = 0
                for value in variant['values']:
                    atributos.append({
                        'atributo':product['attributes'][index]['es'], #Nombre del atributo
                        'valor':value['es'],
                    })
                    index += 1

                #Filtro de product_template_odoo.product_variant_ids el product.product que tenga los mismo atraibutos y valores
                product_variant_odoo = False
                for product_variant in product_template_odoo.product_variant_ids:
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
                        response = requests.get(url_imagen)
                        if response.status_code == 200:
                            image_base64 = base64.b64encode(response.content)
                            product_variant_odoo.image_1920 = image_base64
                

                    #Verificamos si podemos usar el barcode
                    product_barcode_exist = self.env['product.product'].search([('barcode', '=', variant['barcode'])])
                    product_variant_odoo.write({
                        'product_id_tn': variant['id'],
                        'list_price': float(variant['price']) if variant['price'] else 0,
                        'standard_price': float(variant['cost']) if variant['cost'] else 0,
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
                    })

    # Metodo de actualizacion desde Odoo a TN
    def update_product_tn(self, products):
        # Validamos que existan almacenes con location_id_tn
        wharehouse = self.env['stock.warehouse'].sudo().search([('location_id_tn', '!=', False)])
        if len(wharehouse) == 0:
            raise ValidationError('No hay almacenes sincronizados con Tienda Nube, por favor configure al menos un almacén con la ubicación de Tienda Nube')
        headers = self.get_headers_tn()
        for product in products:
            categorias = []
            for category in product.categoria_tn_ids:
                categorias.append(category.tn_id)
            url = "https://api.tiendanube.com/v1/%s/products/%s" % (self.tiendanube_id, product.id_tn)
            data = {
                "categories" : categorias if self.update_product_tn_categories else None,
                "published": product.mostrar_en_tienda_tn if self.update_product_tn_published else None,
                "free_shipping": product.envio_gratis_tn if self.update_product_tn_free_shipping else None,
                "description": product.description_sale if self.update_product_tn_description else None,
                "name": product.name if self.update_product_tn_name else None,
            }
            # Eliminar claves con valor None segun confirguracion de la empresa
            data = {k: v for k, v in data.items() if v is not None}

            response = requests.put(url, headers=headers, json=data)
            if response.status_code != 200:
                raise ValidationError('Error al actualizar producto %s%s en Tienda Nube: %s' % (product.id, product.name, response.text))
            for variant in product.product_variant_ids.filtered(lambda x: x.product_id_tn != False):
                url = "https://api.tiendanube.com/v1/%s/products/%s/variants/%s" % (self.tiendanube_id, product.id_tn, variant.product_id_tn)
                
                price_tn = self.tn_pricelist_id._get_product_price(variant.product_tmpl_id, quantity=1)
                if price_tn is None:
                    price_tn = variant.list_price
                if self.tn_type_tax == 'not_included':
                    price_tn = variant.taxes_id.compute_all(price_tn)['total_included']
                stock_variant = variant.qty_available if self.tn_config_stock == 'stock' else variant.virtual_available
                if stock_variant < 0:
                    stock_variant = 0
                data = {
                    "promotional_price": variant.precio_promocional_tn if self.update_product_tn_promotional_price else None,
                    "weight": variant.peso_tn if self.update_product_tn_dimensions else None,
                    "width": variant.ancho_tn if self.update_product_tn_dimensions else None,
                    "height": variant.alto_tn if self.update_product_tn_dimensions else None,
                    "depth": variant.profundidad_tn if self.update_product_tn_dimensions else None,
                    "sku": variant.default_code if self.update_product_tn_sku else None,
                    "barcode": variant.barcode,
                    "mpn": variant.mpn_tn if self.update_product_tn_mpn else None,
                    "age_group": variant.rango_edad_tn if variant.rango_edad_tn and self.update_product_tn_age_group else None,
                    "gender": variant.sexo_tn if variant.sexo_tn and self.update_product_tn_gender else None,
                    "cost": variant.standard_price if variant.standard_price > 0 and self.update_product_tn_cost else None,
                    "description": variant.product_tmpl_id.description_sale if self.update_product_tn_description else None,
                    "published": variant.product_tmpl_id.mostrar_en_tienda_tn if self.update_product_tn_published else None,
                    "free_shipping": variant.product_tmpl_id.envio_gratis_tn if self.update_product_tn_free_shipping else None,
                    "price": price_tn,
                    "stock": stock_variant,
                }
                # Eliminar claves con valor None segun confirguracion de la empresa
                data = {k: v for k, v in data.items() if v is not None}

                response = requests.put(url, headers=headers, json=data)
                if response.status_code != 200:
                    raise ValidationError('Error al actualizar stock de Tienda Nube: %s' % response.text)
            # Hacemos un commit y procedemos a actulizar stock por warehouse
            self.env.cr.commit()
            # Buscamos los wharehouse que tengan location_id_tn
            location_id_tn = []
            for wh in wharehouse:
                location_id_tn.append(wh.location_id_tn)
            if not location_id_tn[0]:
                return
            # Actualizamos el stock en Tienda Nube
            self.update_product_stock_tn(product, location_id_tn)
            
    # Dividir en lotes de hasta 40 variantes
    def _split_batches(self, products, max_variants):
        batches = []
        current_batch = []
        current_variants_count = 0
        
        for product in products:
            product_variants_count = len(product["variants"])
            
            if current_variants_count + product_variants_count > max_variants:
                batches.append(current_batch)
                current_batch = []
                current_variants_count = 0
            
            current_batch.append(product)
            current_variants_count += product_variants_count
        
        if current_batch:
            batches.append(current_batch)
        
        return batches        
    
    # Metodo de actualizacion de precio desde Odoo a TN    
    def update_product_price_tn(self, products):
        # Contar total de variantes
        total_variants = 0
        for product in products:
            total_variants += len(product.product_variant_ids.filtered(lambda x: x.product_id_tn != False))

        # Si tiene 5 o menos variantes el total de productos, usar ruta individual (PUT)
        if total_variants <= 5:
            self._update_product_price_tn_individual(products)
        else:
            # Si tiene más de 5, usar ruta batch (PATCH) para evitar un limit requests
            self._update_product_price_tn_batch(products)

    def _update_product_price_tn_individual(self, products):
        """Actualiza precios usando PUT individual por variante (para ≤ 5 variantes)"""
        headers = self.get_headers_tn()
        for product in products:
            for variant in product.product_variant_ids.filtered(lambda x: x.product_id_tn != False):
                url = "https://api.tiendanube.com/v1/%s/products/%s/variants/%s" % (
                    self.tiendanube_id, product.id_tn, variant.product_id_tn)

                price_tn = self.tn_pricelist_id._get_product_price(variant.product_tmpl_id, quantity=1)
                if price_tn is None:
                    price_tn = variant.list_price
                if self.tn_type_tax == 'not_included':
                    price_tn = variant.taxes_id.compute_all(price_tn)['total_included']
                data = {
                    "promotional_price": variant.precio_promocional_tn,
                    "cost": variant.standard_price if variant.standard_price > 0 else None,
                    "price": price_tn,
                }
                response = requests.put(url, headers=headers, json=data)
                if response.status_code != 200:
                    raise ValidationError('Error al actualizar precio de Tienda Nube: %s' % response.text)

    def _update_product_price_tn_batch(self, products):
        """Actualiza precios usando PATCH batch (para > 5 variantes)"""
        url = "https://api.tiendanube.com/v1/%s/products/stock-price" % self.tiendanube_id
        headers = self.get_headers_tn()

        data_products = []

        for product in products:
            data_variants = []
            for variant in product.product_variant_ids.filtered(lambda x: x.product_id_tn != False):
                price_tn = self.tn_pricelist_id._get_product_price(variant.product_tmpl_id, quantity=1)
                if price_tn is None:
                    price_tn = variant.list_price
                if self.tn_type_tax == 'not_included':
                    price_tn = variant.taxes_id.compute_all(price_tn)['total_included']

                data_variants.append({
                    'id': int(variant.product_id_tn),
                    "price": price_tn,
                })

            if data_variants:
                data_products.append({
                    'id': int(product.id_tn),
                    'variants': data_variants
                })

        # Dividir en lotes de hasta 40 variantes
        batches = self._split_batches(data_products, 40)

        for batch in batches:
            response = requests.patch(url, headers=headers, json=batch)
            if response.status_code != 200:
                raise ValidationError('Error al actualizar precios de Tienda Nube: %s' % response.text)

    #Actualizamos stock de productos en TN con PATCH /products/stock-price
    def update_product_stock_tn(self, products, location_id_tn):
        # Validamos que existan almacenes con location_id_tn
        wharehouse = self.env['stock.warehouse'].sudo().search([('location_id_tn', '!=', False)])
        if len(wharehouse) == 0:
            raise ValidationError('No hay almacenes sincronizados con Tienda Nube, por favor configure al menos un almacén con la ubicación de Tienda Nube')
        
        url = "https://api.tiendanube.com/v1/%s/products/stock-price" % self.tiendanube_id
        headers = self.get_headers_tn()
        
        # Preparar datos de productos
        data_products = []
        total_variants = 0
        
        for product in products:
            data_variants = []
            for variant in product.product_variant_ids.filtered(lambda x: x.product_id_tn != False):
                for location in location_id_tn:
                    # Obtenemos stock de la ubicacion para el producto filtrando por qty_available o virtual_available para la ubicacion
                    warehouse = self.env['stock.warehouse'].search([('location_id_tn', '=', location)])
                    if warehouse:
                        variant = variant.with_context(warehouse=warehouse.ids)
                    if not variant.stock_ilimitado_tn:
                        stock_variant = int(variant.qty_available) if self.tn_config_stock == 'stock' else int(variant.virtual_available)
                        if stock_variant < 0:
                            stock_variant = 0
                    else:
                        stock_variant = ""
                    data_variants.append({
                        'id': int(variant.product_id_tn),
                        "inventory_levels": [{
                            "location_id": location,
                            "stock": stock_variant,
                        }]
                    })
            
            total_variants += len(data_variants)
            data_products.append({
                'id': int(product.id_tn),
                'variants': data_variants
            })
    
        batches = self._split_batches(data_products, 40)
        
        for batch in batches:
            response = requests.patch(url, headers=headers, json=batch)
            if response.status_code != 200:
                raise ValidationError('Error al actualizar stock de Tienda Nube: %s' % response.text)

    # Obtnenemos todas las categorias de Tienda Nube GET /categories
    def get_all_categories_tn(self):
        url = "https://api.tiendanube.com/v1/%s/categories" % self.tiendanube_id
        headers = self.get_headers_tn()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Segun respuesta crearmos categorias en nuestro modelo category.tn
            for category in data:
                category_odoo = self.env['category.tn'].search([('tn_id', '=', category['id'])])
                parent = False
                # Verificamos si tiene categoria padre, de tener verificamos si existe sino lo creamos
                if category['parent'] != 0:
                    parent_category_odoo = self.env['category.tn'].search([('tn_id', '=', category['parent'])])
                    if parent_category_odoo:
                        parent = parent_category_odoo.id                        


                if not category_odoo:
                    category_odoo = self.env['category.tn'].create({
                        'name': category['name']['es'],
                        'tn_id': category['id'],
                        'parent_id': parent,
                    })
                else:
                    category_odoo.write({
                        'name': category['name']['es'],
                        'parent_id': parent,
                    })
            return data
        else:
            raise ValidationError('Error al obtener categorias de Tienda Nube: %s' % response.text)

    # Metodo para crear el producto en TN POST /products
    def create_product_tn(self, product):
        # Validamos que existan almacenes con location_id_tn
        wharehouse = self.env['stock.warehouse'].sudo().search([('location_id_tn', '!=', False)])
        if len(wharehouse) == 0:
            raise ValidationError('No hay almacenes sincronizados con Tienda Nube, por favor configure al menos un almacén con la ubicación de Tienda Nube')
        headers = self.get_headers_tn()
        url = "https://api.tiendanube.com/v1/%s/products" % self.tiendanube_id

        # Obtenemos url de Odoo desde los parametros de sistema
        url_odoo = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        images = []
        if product.contemplar_imagen_variantes_tn:
            cant_images = 1 # Contador de imagenes, como maximo se pueden subir 9 imagenes a TN
            for variant in product.product_variant_ids:
                if variant.image_1920:
                    images.append({
                        "src": url_odoo + '/ati_tn_product_template_ids/' + str(variant.id),
                    })
                cant_images += 1
                if cant_images == 9:
                    break
        else:
            images.append({
                "src": url_odoo + '/ati_tn_product_template_ids/' + str(product.product_variant_ids[0].id),
            })
        
        #Agregamos imagenes de galeria si existen
        for image_galery in product.product_template_image_tn_ids:
            images.append({
                "src": url_odoo + '/ati_tn_product_template_galery_ids/' + str(image_galery.id),
            })

        categorias = []
        for category in product.categoria_tn_ids:
            categorias.append(category.tn_id)
        variants = []
        attributes = []
        for attribute in product.attribute_line_ids:
            for value in attribute.value_ids:
                if attribute.attribute_id.name in attributes:
                    continue
                attributes.append(attribute.attribute_id.name)
        for variant in product.product_variant_ids:
            if not variant.barcode:
                # Si no tiene codigo de barras le asginamos un EAN-13 temporal verificando que ningun otro producto lo tenga
                temp_barcode = random.randint(2000000000000, 2999999999999)
                while self.env['product.product'].search([('barcode', '=', str(temp_barcode))]):
                    temp_barcode = random.randint(2000000000000, 2999999999999)
                variant.barcode = str(temp_barcode)
            values = []
            for value in variant.product_template_attribute_value_ids:
                values.append(value.name)
            price_tn = self.tn_pricelist_id._get_product_price(variant.product_tmpl_id, quantity=1)
            if price_tn is None:
                price_tn = variant.list_price
            if self.tn_type_tax == 'not_included':
                price_tn = variant.taxes_id.compute_all(price_tn)['total_included']
            stock_variant = variant.qty_available if self.tn_config_stock == 'stock' else variant.virtual_available
            if stock_variant < 0:
                stock_variant = 0
            variants.append({
                "values": values,
                "price": price_tn,
                "promotional_price": variant.precio_promocional_tn,
                "weight": variant.peso_tn,
                "width": variant.ancho_tn,
                "height": variant.alto_tn,
                "depth": variant.profundidad_tn,
                "sku": variant.default_code,
                "barcode": variant.barcode,
                "mpn": variant.mpn_tn,
                "age_group": variant.rango_edad_tn if variant.rango_edad_tn else None,
                "gender": variant.sexo_tn if variant.sexo_tn else None,
                "cost": variant.standard_price if variant.standard_price > 0 else None,
                "stock_management": True,
                "stock": stock_variant,
            })
        data = {
            "name": product.name,
            "description": product.description_sale,
            "variants": variants,
            "published": product.mostrar_en_tienda_tn,
            "free_shipping": product.envio_gratis_tn,
            "categories": categorias,
            "attributes": attributes,
            "images": images,
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            data = response.json()
            product.id_tn = data['id']
            product.canonical_url = data['canonical_url']
            #asignamos el id de Tienda Nube a cada variante
            # Variable position para utilizar como bandera e identificar la posicion de las imagenes en el arreglo image devuelto
            position = 0
            for v in data['variants']:
                variant = product.product_variant_ids.filtered(lambda x: x.barcode.replace(' ', '') == v['barcode'])
                variant.product_id_tn = v['id']
                # Si se contemplan imagenes por variantes, asignamos la imagen correspondiente a la variante
                if product.contemplar_imagen_variantes_tn and 'images' in data and len(data['images']) > 0:
                    #Modificamos la imagenes de la variante en tienda nube
                    url_put_image = "https://api.tiendanube.com/v1/%s/products/%s/variants/%s" % (self.tiendanube_id, v['product_id'], v['id'])
                    data_variant_image = {
                        "image_id": data['images'][position]['id'],
                    }
                    response_image_variant = requests.put(url_put_image, headers=headers, json=data_variant_image)
                position += 1
                # [images] siempre trae como maximo 8 imagenes, por lo que si hay mas variantes no se asignan imagenes y debemos hacer un break para evitar un "list index out of range"
                if position >= 8:
                    break

        else:
            raise ValidationError('Error al crear producto en Tienda Nube: %s' % response.text)
        # Hacemos un commit y procedemos a actulizar stock por warehouse
        self.env.cr.commit()
        # Buscamos los wharehouse que tengan location_id_tn
        location_id_tn = []
        for wh in wharehouse:
            location_id_tn.append(wh.location_id_tn)
        if not location_id_tn[0]:
            return
        # Actualizamos el stock en Tienda Nube
        self.update_product_stock_tn(product, location_id_tn)


    # Metodo para obtener webooks de Tienda Nube
    def get_webhooks_tn(self):
        url = "https://api.tiendanube.com/v1/%s/webhooks" % self.tiendanube_id
        headers = self.get_headers_tn()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Segun respuesta crearmos webhooks en nuestro modelo webhook.tn
            for webhook in data:
                webhook_odoo = self.env['webhook.tn'].search([('id_webhook_tn', '=', webhook['id'])])
                if not webhook_odoo:
                    webhook_odoo = self.env['webhook.tn'].create({
                        'name': webhook['event'],
                        'id_webhook_tn': webhook['id'],
                        'url': webhook['url'],
                        'event': webhook['event'],
                        'created_at_tn': datetime.datetime.strptime(webhook['created_at'], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None),
                        'updated_at_tn': datetime.datetime.strptime(webhook['updated_at'], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None),
                    })
                else:
                    webhook_odoo.write({
                        'url': webhook['url'],
                        'event': webhook['event'],
                        'created_at_tn': datetime.datetime.strptime(webhook['created_at'], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None),
                        'updated_at_tn': datetime.datetime.strptime(webhook['updated_at'], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None),
                    })
        else:
            raise ValidationError('Error al obtener webhooks de Tienda Nube: %s' % response.text)

    # Metodo para obtener cupones de Tienda Nube
    def get_all_coupon_tn(self):
        url = "https://api.tiendanube.com/v1/%s/coupons" % self.tiendanube_id
        headers = self.get_headers_tn()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Segun respuesta crearmos cupones en nuestro modelo coupon.tn
            for coupon in data:
                coupon_odoo = self.env['coupon.tn'].search([('id_tn', '=', coupon['id'])])
                if not coupon_odoo:
                    coupon_odoo = self.env['coupon.tn'].create({
                        'name': coupon['code'],
                        'id_tn': coupon['id'],
                        'type_tn': coupon['type'],
                        'value': coupon['value'],
                        'valid': coupon['valid'],
                        'max_use': coupon['max_uses'],
                        'includes_shipping': coupon['includes_shipping'],
                        'min_price': coupon['min_price'],
                        'start_date': coupon['start_date'],
                        'end_date': coupon['end_date'],
                        'used': coupon['used'],
                    })
                else:
                    coupon_odoo.write({
                        'name': coupon['code'],
                        'type_tn': coupon['type'],
                        'value': coupon['value'],
                        'valid': coupon['valid'],
                        'max_use': coupon['max_uses'],
                        'includes_shipping': coupon['includes_shipping'],
                        'min_price': coupon['min_price'],
                        'start_date': coupon['start_date'],
                        'end_date': coupon['end_date'],
                        'used': coupon['used'],
                    })
                # Creamos log de TN
                self.env['tn.log'].create_log(
                    name='Cupon creado/actualizado en Odoo desde TN con id %s' % coupon['id'],
                    message=coupon,
                    model='coupon.tn',
                    model_id=coupon_odoo.id,
                    level='success',
                )

    # Metodo para traer ordenes de Tienda Nube a Odoo
    def get_all_orders_tn(self):
        url = "https://api.tiendanube.com/v1/%s/orders?fields=id" % self.tiendanube_id
        headers = self.get_headers_tn()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Segun respuesta crearmos ordenes en nuestro modelo sale.order
            for order in data:
                order_odoo = self.env['sale.order'].search([('id_tn', '=', order['id'])])
                if not order_odoo:
                    order_odoo = self.env['sale.order'].create({
                        'id_tn': order['id'],
                        'partner_id': self.env.ref('base.public_partner').id,
                    }).create_order_from_tn()
        else:
            # Creamos log de TN
            self.env['tn.log'].create_log(
                name='Error al obtener ordenes de Tienda Nube',
                message='Error desde Company',
                model='res.company',
                model_id=self.id,
                level='error',
                error_tn=response.text,
            )
            raise ValidationError('Error al obtener ordenes de Tienda Nube: %s' % response.text)

    # Metodo para traer Almacenes y Ubicaciones de Tienda Nube a Odoo
    def get_location_tn(self):
        url = "https://api.tiendanube.com/v1/%s/locations" % self.tiendanube_id
        headers = self.get_headers_tn()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return False
