import logging
import requests
import base64
                
from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class SaleOrderTiendaNubeInherit(models.Model):
    _inherit = "sale.order"

    id_tn = fields.Char('ID Tienda Nube', help="ID de Tienda Nube", copy=False)
    number_tn = fields.Char('Numero de orden', help="Numero de orden de Tienda Nube", copy=False)
    token_tn = fields.Char('Token Tienda Nube', help="Token de Tieanda Nube", copy=False)
    store_id_tn = fields.Char('Store ID Tienda Nube', help="Store ID de Tienda Nube", copy=False)
    contact_email_tn = fields.Char('Email de contacto', help="Email de Tienda Nube", copy=False)
    contact_name_tn = fields.Char('Nombre de contacto', help="Nombre de Tienda Nube", copy=False)
    contact_phone_tn = fields.Char('Telefono de contacto', help="Telefono de Tienda Nube", copy=False)
    contact_identification_tn = fields.Char('Identificacion de contacto', help="Identificacion de Tienda Nube", copy=False)
    shipping_min_days_tn = fields.Char('Minimo de dias de envio', help="Minimo de dias de envio de Tienda Nube", copy=False)
    shipping_max_days_tn = fields.Char('Maximo de dias de envio', help="Maximo de dias de envio de Tienda Nube", copy=False)
    billing_name_tn = fields.Char('Nombre de facturacion', help="Nombre de facturacion de Tienda Nube", copy=False)
    billing_phone_tn = fields.Char('Telefono de facturacion', help="Telefono de facturacion de Tienda Nube", copy=False)
    billing_address_tn = fields.Char('Direccion de facturacion', help="Direccion de facturacion de Tienda Nube", copy=False)
    billing_number_tn = fields.Char('Numero', help="Numero Direccion de facturacion de Tienda Nube", copy=False)
    billing_floor_tn = fields.Char('Piso', help="Piso Direccion de facturacion de Tienda Nube", copy=False)
    billing_locality_tn = fields.Char('Localidad', help="Localidad Direccion de facturacion de Tienda Nube", copy=False)
    billing_zipcode_tn = fields.Char('Codigo Postal', help="Codigo Postal Direccion de facturacion de Tienda Nube", copy=False)
    billing_city_tn = fields.Char('Ciudad', help="Ciudad Direccion de facturacion de Tienda Nube", copy=False)
    billing_province_tn = fields.Char('Provincia', help="Provincia Direccion de facturacion de Tienda Nube", copy=False)
    billing_country_tn = fields.Char('Pais', help="Pais Direccion de facturacion de Tienda Nube", copy=False)
    billing_customer_type_tn = fields.Char('Tipo de cliente', help="Tipo de cliente de Tienda Nube", copy=False)
    billing_business_name_tn = fields.Char('Razon Social', help="Razon Social de Tienda Nube", copy=False)
    billing_trade_name_tn = fields.Char('Nombre Comercial', help="Nombre Comercial de Tienda Nube", copy=False)
    billing_state_registration_tn = fields.Char('Inscripcion Estatal', help="Inscripcion Estatal de Tienda Nube", copy=False)
    billing_document_type_tn = fields.Char('Tipo de documento', help="Tipo de documento de Tienda Nube", copy=False)
    
    # Shipping
    shipping_min_days_tn = fields.Char('Minimo de dias de envio', help="Minimo de dias de envio de Tienda Nube", copy=False)
    shipping_max_days_tn = fields.Char('Maximo de dias de envio', help="Maximo de dias de envio de Tienda Nube", copy=False)
    shipping_cost_owner_tn = fields.Float('Costo de envio propietario', help="Costo de envio propietario de Tienda Nube", copy=False)
    shipping_cost_customer_tn = fields.Float('Costo de envio cliente', help="Costo de envio cliente de Tienda Nube", copy=False)
    shipping_tn = fields.Char('Envio', help="Envio de Tienda Nube", copy=False)
    shipping_option_tn = fields.Char('Opcion de envio', help="Opcion de envio de Tienda Nube", copy=False)
    shipping_option_code_tn = fields.Char('Codigo de opcion de envio', help="Codigo de opcion de envio de Tienda Nube", copy=False)
    shipping_option_reference_tn = fields.Char('Referencia de opcion de envio', help="Referencia de opcion de envio de Tienda Nube", copy=False)
    shipping_pickup_details_tn = fields.Char('Detalles de recoleccion', help="Detalles de recoleccion de Tienda Nube", copy=False)
    shipping_tracking_number_tn = fields.Char('Numero de seguimiento', help="Numero de seguimiento de Tienda Nube", copy=False)
    shipping_tracking_url_tn = fields.Char('URL de seguimiento', help="URL de seguimiento de Tienda Nube", copy=False)
    shipping_store_branch_name_tn = fields.Char('Nombre de sucursal', help="Nombre de sucursal de Tienda Nube", copy=False)
    shipping_store_branch_extra_tn = fields.Char('Extra de sucursal', help="Extra de sucursal de Tienda Nube", copy=False)
    shipping_pickup_type_tn = fields.Char('Tipo de recoleccion', help="Tipo de recoleccion de Tienda Nube", copy=False)

    coupon_tn_ids = fields.Many2many('coupon.tn', string='Cupones Tienda Nube', help="Cupones de Tienda Nube", readonly=True)
    promotions_applied_tn = fields.Text('Promociones aplicadas', help="Promociones aplicadas de Tienda Nube", copy=False)

    json_tn = fields.Text('JSON Tienda Nube', help="JSON de Tienda Nube", copy=False)

    # Metodo para crear la orden en Odoo desde TN GET /orders/{id}
    def create_order_from_tn(self):
        try:
            _logger.info("Create Order from TN")
            company = self.env.user.company_id
            headers = company.get_headers_tn()
            url = "https://api.tiendanube.com/v1/%s/orders/%s" % (company.tiendanube_id, self.id_tn)
            response = requests.get(url, headers=headers)
            _logger.info("Response: %s", response.text)
            if response.status_code == 200:
                order = response.json()
                _logger.info("Data: %s", order)

                # Datos de la orden
                _logger.info("********** Intento 1")
                created_at = datetime.strptime(order['created_at'], '%Y-%m-%dT%H:%M:%S%z')
                _logger.info("********** Intento 2")
                self.date_order = created_at.strftime('%Y-%m-%d %H:%M:%S')
                _logger.info("********** Intento 3")
                self.json_tn = order
                self.id_tn = order['id']
                self.number_tn = order['number']
                self.token_tn = order['token']
                self.store_id_tn = order['store_id']
                self.contact_email_tn = order['contact_email']
                self.contact_name_tn = order['contact_name']
                self.contact_phone_tn = order['contact_phone']
                self.contact_identification_tn = order['contact_identification']
                self.shipping_min_days_tn = order['shipping_min_days']
                self.shipping_max_days_tn = order['shipping_max_days']
                self.billing_name_tn = order['billing_name']
                self.billing_phone_tn = order['billing_phone']
                self.billing_address_tn = order['billing_address']
                self.billing_number_tn = order['billing_number']
                self.billing_floor_tn = order['billing_floor']
                self.billing_locality_tn = order['billing_locality']
                self.billing_zipcode_tn = order['billing_zipcode']
                self.billing_city_tn = order['billing_city']
                self.billing_province_tn = order['billing_province']
                self.billing_country_tn = order['billing_country']
                self.billing_customer_type_tn = order['billing_customer_type'] if order['billing_customer_type'] != "None" else False
                self.billing_business_name_tn = order['billing_business_name'] if order['billing_business_name'] != "None" else False
                self.billing_trade_name_tn = order['billing_trade_name'] if order['billing_trade_name'] != "None" else False
                self.billing_state_registration_tn = order['billing_state_registration'] if order['billing_state_registration'] != "None" else False
                self.billing_document_type_tn = order['billing_document_type'] if order['billing_document_type'] != "None" else False
                self.shipping_cost_owner_tn = float(order['shipping_cost_owner'])
                self.shipping_cost_customer_tn = float(order['shipping_cost_customer'])
                self.shipping_tn = order['shipping']
                self.shipping_min_days_tn = order['shipping_min_days']
                self.shipping_max_days_tn = order['shipping_max_days']
                self.shipping_option_tn = order['shipping_option']
                self.shipping_option_code_tn = order['shipping_option_code']
                self.shipping_option_reference_tn = order['shipping_option_reference']
                self.shipping_pickup_details_tn = order['shipping_pickup_details']
                self.shipping_tracking_number_tn = order['shipping_tracking_number']
                self.shipping_tracking_url_tn = order['shipping_tracking_url']
                self.shipping_store_branch_name_tn = order['shipping_store_branch_name']
                self.shipping_store_branch_extra_tn = order['shipping_store_branch_extra']
                self.shipping_pickup_type_tn = order['shipping_pickup_type']

                # Buscamos el cliente
                partner = self.env['res.partner']
                if order['contact_identification'] != None:
                    partner = self.env['res.partner'].search([('vat', '=', order['contact_identification'])], limit=1)
                elif order['contact_email'] != None:
                    partner = self.env['res.partner'].search([('email', '=', order['contact_email'])], limit=1)
                if not partner:
                    partner = self.env['res.partner'].create({
                        'name': order['customer']['name'] if 'customer' in order else order['contact_name'],
                        'email': order['customer']['email'] if 'customer' in order else order['contact_email'],
                        'phone': order['customer']['phone'] if 'customer' in order else order['contact_phone'],
                        'vat': order['customer']['identification'] if 'customer' in order else order['contact_identification'],
                        'company_type': 'person',
                    })
                self.partner_id = partner.id
                
                # Completamos lineas de la orden
                for line in order['products']:
                    _logger.info("Line: %s", line['product_id'])
                    product = self.env['product.product'].search([('product_id_tn', '=', line['variant_id'])], limit=1)
                    
                    if not product:
                        self.env.cr.rollback()
                        raise ValidationError(_("Producto '{0}' con codigo '{1}' en Tienda Nuve no encontrado en Odoo".format(line['name'], line['variant_id'])))
                    
                    self.env['sale.order.line'].create({
                        'name': line['name'],
                        'order_id': self.id,
                        'product_id': product.id,
                        'product_uom_qty': float(line['quantity']),
                        'price_unit': float(line['price']),
                    })

                # DESCUENTOS
                if len(order['coupon']) or len(order['promotional_discount']['promotions_applied']):
                    product_discount_tn = self.env.ref('tiendanube_odoo.product_discount_tn')
                    if not product_discount_tn:
                        raise ValidationError(_("Producto de descuento no encontrado en Odoo"))
                    # Agregamos seccion de descuento en Sale Order
                    self.write(
                        {'order_line':[(0, 0, {
                            'display_type': 'line_section',
                            'name': 'Descuentos Aplicados',
                            })]
                        }
                    )

                    # Verificamos por cupones de descuento
                    _logger.info("************** Coupons1: %s", order['coupon'])
                    for coupon in order['coupon']:
                        coupon_tn = self.env['coupon.tn'].search([('id_tn', '=', coupon['id'])], limit=1)
                        if not coupon_tn:
                            coupon_tn = self.env['coupon.tn'].create({
                                'id_tn': coupon['id'],
                                'name': coupon['code'],
                                'type_tn': coupon['type'],
                                'value': coupon['value'],
                                'valid': coupon['valid'],
                                'max_use': coupon['max_uses'],
                                'includes_shipping': coupon['includes_shipping'],
                                'min_price': coupon['min_price'],
                                'start_date': coupon['start_date'],
                                'end_date': coupon['end_date'],
                            })
                        self.coupon_tn_ids = [(4, coupon_tn.id)]
                        self.env['sale.order.line'].create({
                            'name': 'Descuento por cupón (' + coupon['code'] + ')',
                            'order_id': self.id,
                            'product_id': product_discount_tn.id,
                            'product_uom_qty': -1,
                            'price_unit': order['discount_coupon'],
                        }).write({'tax_id': False})
                    # Verificamos por promociones aplicadas
                    _logger.info("************** Promotions: %s", order['promotional_discount'])
                    if 'promotions_applied' in order['promotional_discount']:
                        for promotions_applied in order['promotional_discount']['promotions_applied']:
                            _logger.info("************** promotions_applied: %s", promotions_applied)
                            if self.promotions_applied_tn:
                                self.promotions_applied_tn += "Tipo: " + promotions_applied['discount_script_type'] + " - Descuento: " + promotions_applied['total_discount_amount_short'] + "\n"
                            else:
                                self.promotions_applied_tn = "Tipo: " + promotions_applied['discount_script_type'] + " - Descuento: " + promotions_applied['total_discount_amount_short'] + "\n"
                            self.env['sale.order.line'].create({
                                'name': 'Promoción ' + promotions_applied['discount_script_type'],
                                'order_id': self.id,
                                'product_id': product_discount_tn.id,
                                'product_uom_qty': -1,
                                'price_unit': promotions_applied['total_discount_amount'],
                            }).write({'tax_id': False})

                # Creamos un log
                self.env['tn.log'].create_log('Orden de venta {0} creada'.format(self.name), 'Orden de Venta creada desde Tienda Nube', 'sale.order', self.id, 'success')
            else:
                # Creamos un log
                self.env['tn.log'].create_log('No se pudo crear Orden de Venta', 'Error al obtener orden de Tienda Nube', 'sale.order', self.id, 'error', response.text)
        except Exception as e:
            # Creamos un log
            self.env['tn.log'].create_log('No se pudo crear Orden de Venta', str(e), 'sale.order', self.id, 'error')
