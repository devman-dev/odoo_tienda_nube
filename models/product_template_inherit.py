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
    canonical_url = fields.Char('URL Publica', help="URL Publica del producto en Tienda Nube")
    #Campos de variables
    stock_ilimitado_tn = fields.Boolean('Stock Ilimitado en Tienda Nube', help="Stock Ilimitado en Tienda Nube", compute='_compute_stock_ilimitado_tn', inverse='_set_stock_ilimitado_tn')
    precio_promocional_tn = fields.Float('Precio Promocional Tienda Nube', help="Precio promocional de Tienda Nube", compute='_compute_precio_promocional_tn', inverse='_set_precio_promocional_tn')
    #Dimensiones TN
    alto_tn = fields.Float('Alto en CM', help="Alto en Tienda Nube", compute='_compute_alto_tn', inverse='_set_alto_tn')
    ancho_tn = fields.Float('Ancho en CM', help="Ancho en Tienda Nube", compute='_compute_ancho_tn', inverse='_set_ancho_tn')
    profundidad_tn = fields.Float('Profundidad en CM', help="Profundidad en Tienda Nube", compute='_compute_profundidad_tn', inverse='_set_profundidad_tn')
    peso_tn = fields.Float('Peso en Kg', help="Peso en Tienda Nube", compute='_compute_peso_tn', inverse='_set_peso_tn')
    #Instagram y Google Shopping
    mpn_tn = fields.Char('MPN', help="MPN (Número de pieza del fabricante) en Tienda Nube", compute='_compute_mpn_tn', inverse='_set_mpn_tn')
    rango_edad_tn = fields.Selection([
        ('newborn', '0-3 Meses'),
        ('infant', '3-12 Meses'),
        ('toddler', '1-5 Años'),
        ('kids', '5-13 Años'),
        ('adult', 'Adulto'),
    ], string='Rango de Edad', help="Rango de Edad en Tienda Nube", compute='_compute_rango_edad_tn', inverse='_set_rango_edad_tn')
    sexo_tn = fields.Selection([
        ('unisex', 'Unisex'),
        ('male', 'Masculino'),
        ('female', 'Femenino'),
    ], string='Sexo', help="Sexo en Tienda Nube", default='unisex', compute='_compute_sexo_tn', inverse='_set_sexo_tn')
    contemplar_imagen_variantes_tn = fields.Boolean('Contemplar imagen de variantes en Tienda Nube', help="Indica si se debe contemplar la imagen de las variantes al crear el producto o actualizar imagenes en Tienda Nube", default=True)
    product_template_image_tn_ids = fields.One2many('product.image.tn', 'product_tmpl_tn_id', 'Imagenes de Tienda Nube', help="Imagenes del producto en Tienda Nube", copy=True)
    # stock_ilimitado_tn
    @api.depends('product_variant_ids.stock_ilimitado_tn')
    def _compute_stock_ilimitado_tn(self):
        self.stock_ilimitado_tn = False
        for template in self:
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.stock_ilimitado_tn = template.product_variant_ids.stock_ilimitado_tn
            elif variant_count == 0:
                archived_variants = template.with_context(active_test=False).product_variant_ids
                if len(archived_variants) == 1:
                    template.stock_ilimitado_tn = archived_variants.stock_ilimitado_tn
    def _set_stock_ilimitado_tn(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.stock_ilimitado_tn = self.stock_ilimitado_tn
        elif variant_count == 0:
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.stock_ilimitado_tn = self.stock_ilimitado_tn
    # precio_promocional_tn
    @api.depends('product_variant_ids.precio_promocional_tn')
    def _compute_precio_promocional_tn(self):
        self.precio_promocional_tn = False
        for template in self:
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.precio_promocional_tn = template.product_variant_ids.precio_promocional_tn
            elif variant_count == 0:
                archived_variants = template.with_context(active_test=False).product_variant_ids
                if len(archived_variants) == 1:
                    template.precio_promocional_tn = archived_variants.precio_promocional_tn
    def _set_precio_promocional_tn(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.precio_promocional_tn = self.precio_promocional_tn
        elif variant_count == 0:
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.precio_promocional_tn = self.precio_promocional_tn
    # sexo_tn
    @api.depends('product_variant_ids.sexo_tn')
    def _compute_sexo_tn(self):
        self.sexo_tn = False
        for template in self:
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.sexo_tn = template.product_variant_ids.sexo_tn
            elif variant_count == 0:
                archived_variants = template.with_context(active_test=False).product_variant_ids
                if len(archived_variants) == 1:
                    template.sexo_tn = archived_variants.sexo_tn
    def _set_sexo_tn(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.sexo_tn = self.sexo_tn
        elif variant_count == 0:
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.sexo_tn = self.sexo_tn
    # rango_edad_tn
    @api.depends('product_variant_ids.rango_edad_tn')
    def _compute_rango_edad_tn(self):
        self.rango_edad_tn = False
        for template in self:
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.rango_edad_tn = template.product_variant_ids.rango_edad_tn
            elif variant_count == 0:
                archived_variants = template.with_context(active_test=False).product_variant_ids
                if len(archived_variants) == 1:
                    template.rango_edad_tn = archived_variants.rango_edad_tn
    def _set_rango_edad_tn(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.rango_edad_tn = self.rango_edad_tn
        elif variant_count == 0:
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.rango_edad_tn = self.rango_edad_tn
    # mpn_tn
    @api.depends('product_variant_ids.mpn_tn')
    def _compute_mpn_tn(self):
        self.mpn_tn = False
        for template in self:
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.mpn_tn = template.product_variant_ids.mpn_tn
            elif variant_count == 0:
                archived_variants = template.with_context(active_test=False).product_variant_ids
                if len(archived_variants) == 1:
                    template.mpn_tn = archived_variants.mpn_tn
    def _set_mpn_tn(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.mpn_tn = self.mpn_tn
        elif variant_count == 0:
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.mpn_tn = self.mpn_tn
    # alto_tn
    @api.depends('product_variant_ids.alto_tn')
    def _compute_alto_tn(self):
        self.alto_tn = False
        for template in self:
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.alto_tn = template.product_variant_ids.alto_tn
            elif variant_count == 0:
                archived_variants = template.with_context(active_test=False).product_variant_ids
                if len(archived_variants) == 1:
                    template.alto_tn = archived_variants.alto_tn
    def _set_alto_tn(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.alto_tn = self.alto_tn
        elif variant_count == 0:
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.alto_tn = self.alto_tn
    #ancho_tn
    @api.depends('product_variant_ids.ancho_tn')
    def _compute_ancho_tn(self):
        self.ancho_tn = False
        for template in self:
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.ancho_tn = template.product_variant_ids.ancho_tn
            elif variant_count == 0:
                archived_variants = template.with_context(active_test=False).product_variant_ids
                if len(archived_variants) == 1:
                    template.ancho_tn = archived_variants.ancho_tn
    def _set_ancho_tn(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.ancho_tn = self.ancho_tn
        elif variant_count == 0:
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.ancho_tn = self.ancho_tn
    #profundidad_tn
    @api.depends('product_variant_ids.profundidad_tn')
    def _compute_profundidad_tn(self):
        self.profundidad_tn = False
        for template in self:
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.profundidad_tn = template.product_variant_ids.profundidad_tn
            elif variant_count == 0:
                archived_variants = template.with_context(active_test=False).product_variant_ids
                if len(archived_variants) == 1:
                    template.profundidad_tn = archived_variants.profundidad_tn
    def _set_profundidad_tn(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.profundidad_tn = self.profundidad_tn
        elif variant_count == 0:
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.profundidad_tn = self.profundidad_tn
    #peso_tn
    @api.depends('product_variant_ids.peso_tn')
    def _compute_peso_tn(self):
        self.peso_tn = False
        for template in self:
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.peso_tn = template.product_variant_ids.peso_tn
            elif variant_count == 0:
                archived_variants = template.with_context(active_test=False).product_variant_ids
                if len(archived_variants) == 1:
                    template.peso_tn = archived_variants.peso_tn
    def _set_peso_tn(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.peso_tn = self.peso_tn
        elif variant_count == 0:
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.peso_tn = self.peso_tn

    # Sobreescribimos unlink para que no se pueda borrar producto de descuento de Tienda Nube
    def unlink(self):
        product_discount_tn = self.env.ref('odoo_tienda_nube.product_discount_tn_product_template')
        product_shipping_tn = self.env.ref('odoo_tienda_nube.product_shipping_tn_product_template')
        for product in self:
            if product.id == product_discount_tn.id:
                raise ValidationError(_("No se puede borrar el producto de descuento de Tienda Nube"))
            if product.id == product_shipping_tn.id:
                raise ValidationError(_("No se puede borrar el producto de envío de Tienda Nube"))
        return super(TiendaNubeProductTemplateInherit, self).unlink()

    # Metodo de actualizacion de imagenes desde Odoo a TN
    def update_product_image_tn(self):
        for product in self:
            if product.id_tn:
                # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
                company = self.env.company if self.env.company else self.env.user.company_id
                company.update_product_images_tn(product)

    # Metodo de actualizacion desde Odoo a TN
    def update_tn(self):
        for product in self:
            if product.id_tn:
                # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
                company = self.env.company if self.env.company else self.env.user.company_id
                company.update_product_tn(product)
    
    # Metodo de actualizacion de precio desde Odoo a TN
    def update_price_tn(self):
        for product in self:
            if product.id_tn:
                # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
                company = self.env.company if self.env.company else self.env.user.company_id
                company.update_product_price_tn(product)

    # Metodo de actualizacion de stock desde Odoo a TN
    def update_stock_tn(self):
        for product in self:
            if product.id_tn:
                # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
                company = self.env.company if self.env.company else self.env.user.company_id
                #Obtenemos los almacenes de la compañia que tenga location_id_tn
                warehouses = self.env['stock.warehouse'].search([('location_id_tn', '!=', False)])
                location_id_tn = []
                for warehouse in warehouses:
                    location_id_tn.append(warehouse.location_id_tn)
                if len(location_id_tn) == 0:
                    return

                company.update_product_stock_tn(product, location_id_tn)

    # Metodo para crear el producto en TN
    def create_tn(self):
        for product in self:
            if not product.id_tn:
                # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
                company = self.env.company if self.env.company else self.env.user.company_id
                company.create_product_tn(product)

    # Metodo para desvincular producto de Tienda Nube
    def unlink_tn(self):
        for product in self:
            for v in product.product_variant_ids:
                v.write({
                    'product_id_tn': False,
                })

            product.write({
                'id_tn': False,
            })

    # Metodo para crear/actualizar producto en Odoo desde TN por medio de id GET /products/{id}
    def create_update_product_from_tn(self):

        if self.env.context.get('company_id'):
            company = self.env['res.company'].browse(self.env.context.get('company_id'))
        else:
            # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
            company = self.env.company if self.env.company else self.env.user.company_id
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

            self.name = product['name']['es']
            self.description_sale = product['description']['es']
            self.id_tn = product['id']
            self.envio_gratis_tn = product['free_shipping']
            self.mostrar_en_tienda_tn = product['published']
            self.categoria_tn_ids = [(6, 0, categoria_tn_ids)]
            self.image_1920 = image_template_base64
            self.type = 'consu' if product['requires_shipping'] else 'service'
            self.is_storable = True if product['requires_shipping'] else False
            
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
                    })



        else:
            raise ValidationError(_("Error al crear el producto"))

