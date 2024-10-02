# -*- coding: utf-8 -*-
import logging
import hmac
import hashlib
from odoo.tools import base64

import odoo
import json
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)
CORS = '*'
CLIENT_SECRET = 'cb98cf7830c4e366a962ac56e554c12d9c4c188ed1f2ab62'

class TiendaNubeWebHook(http.Controller):

    # https://tiendanube.github.io/api-documentation/resources/webhook#rules-for-deduplication
    # verificamos segun 3 segundos de diferencia en creacion del ultimo webhook igual
    def duplicity_check(self, data):
        webhook_received = request.env['webhook.tn.received'].sudo().search([
            ('id_event_tn','=',data['id']),('event','=',data['event']),('store_id','=',data['store_id'])
            ],limit=1, order='create_date desc')
        _logger.info('******* webhook_received: %s' % webhook_received)
        _logger.info('******* odoo.fields.Datetime.now: %s' % odoo.fields.Datetime.now())
        _logger.info('******* webhook_received.create_date: %s' % webhook_received.create_date)
        if webhook_received and (odoo.fields.Datetime.now() - webhook_received.create_date).seconds < 3:
            return True
        return False

    def verify_webhook(self, data, hmac_header):
        calculated_hmac = hmac.new(CLIENT_SECRET.encode('utf-8'), data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(calculated_hmac, hmac_header)

    #Controller para descargar adjuntos
    @http.route('/webhook_tn/<string:code_event>', auth='public', cors=CORS, csrf=False)
    def TiendaNubeWebHook(self, **kw):

        
        # Verificación de locking
        lock_name = 'webhook_processing'
        if request.env['ir.config_parameter'].sudo().get_param(lock_name) == 'En uso':
            _logger.info('******* lock_name encontrado y rebotado')
            return request.make_response(
                json.dumps({"mensaje": "Otra solicitud está en proceso"}),
                headers={'Content-Type': 'application/json'},
                status=429
            )
        
        request.env['ir.config_parameter'].sudo().set_param(lock_name, 'En uso')
        # Como puede darse la posibilidad de que entren mas rapido webhook duplicados que la velocidad de creacion de un webhook.tn.received
        # creamos este parametro de sistema para controlar si se esta usando el endpoint webhook_tn, de estar en uso rebotamos cualquier solicitud
        # hasta que se resuelva la que esta en proceso
        request.env.cr.commit()
        try:

            data = json.loads(request.httprequest.get_data())

            # Verificacion de duplicidad
            if self.duplicity_check(data):
                return request.make_response(
                    json.dumps({"mensaje": "Operación duplicada"}),
                    headers={'Content-Type': 'application/json'},
                    status=200
                )
            else:
                # Creamos el registro webhook.tn.received
                request.env['webhook.tn.received'].sudo().create({
                    'name': 'Evento: ' + data['event'] + ' - ID: ' + str(data['id']) + ' - Store ID:' + str(data['store_id']),
                    'id_event_tn': data['id'],
                    'event': data['event'],
                    'store_id': data['store_id'],
                })
                request.env.cr.commit()

            # Encabezado HMAC de la solicitud para verificar la autenticidad de la solicitud
            hmac_header = request.httprequest.headers.get('X-LINKEDSTORE-HMAC-SHA256')
            if not hmac_header:
                hmac_header = request.httprequest.headers.get('HTTP-X-LINKEDSTORE-HMAC-SHA256')
            if self.verify_webhook(request.httprequest.get_data(), hmac_header):
                _logger.info('*********** HMAC correcto')
            else:
                _logger.info('*********** HMAC incorrecto')
                return request.make_response(
                    json.dumps({"mensaje": "Firma incorrecta"}),
                    headers={'Content-Type': 'application/json'},
                    status=400
                )

            if 'code_event' in kw:
                code_event = kw['code_event']
                _logger.info('code_event: %s' % code_event)
                webhook = request.env['webhook.tn'].sudo().search([
                    ('url','=',request.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/webhook_tn/' + code_event)
                    ],limit=1)
                exitoso = False
                if webhook:
                    #CATEGORIAS
                    #category/updated
                    if webhook.event == 'category/updated':
                        category = request.env['category.tn'].sudo().search([
                            ('tn_id','=',data['id'])
                            ],limit=1)
                        if category:
                            category.sudo().update_category_tn_odoo()
                        exitoso = True
                        
                    #category/created
                    elif webhook.event == 'category/created':
                        #Creamos la/s categoria/s nueva/s
                        request.env.company.sudo().get_all_categories_tn()
                        exitoso = True
                    #category/deleted
                    elif webhook.event == 'category/deleted':
                        category = request.env['category.tn'].sudo().search([
                            ('tn_id','=',data['id'])
                            ],limit=1)
                        if category:
                            category.sudo().unlink()
                        exitoso = True
                    #PRODUCTOS
                    #product/deleted
                    elif webhook.event == 'product/deleted':
                        product = request.env['product.template'].sudo().search([
                            ('id_tn','=',data['id'])
                            ],limit=1)
                        if product:
                            product.sudo().write({
                                'active': False,
                                'name': product.name + ' #Producto eliminado desde Tienda Nube',
                                'barcode': False,
                                'default_code': False,
                            })
                        exitoso = True
                    #product/create
                    elif webhook.event == 'product/created':
                        try:
                            #Buscamos el producto en Odoo y si no existe lo creamos
                            product = request.env['product.template'].sudo().search([
                                ('id_tn','=',data['id'])
                                ],limit=1)
                            if not product:
                                product = request.env['product.template'].sudo().create({
                                    'id_tn': data['id'],
                                    'name': 'Nuevo Producto TN id: ' + str(data['id']),
                                })
                            product.sudo().create_update_product_from_tn()
                            exitoso = True
                        except Exception as e:
                            _logger.info('*********** Error: %s' % e)
                            return request.make_response(
                                json.dumps({"mensaje": "Error al crear el producto"}),
                                headers={'Content-Type': 'application/json'},
                                status=500
                            )
                    #product/updated
                    elif webhook.event == 'product/updated':
                        product = request.env['product.template'].sudo().search([
                            ('id_tn','=',data['id'])
                            ],limit=1)
                        # Para evitar un bucle infinito verificamos si el producto fue actualizado desde Odoo hacia tienda nube
                        # con un tiempo de 2 min suponiendo que mas que esto no demorarian los webhooks
                        if product and (odoo.fields.Datetime.now() - product.write_date).seconds > 120:
                            try:
                                product.sudo().create_update_product_from_tn()
                            except Exception as e:
                                _logger.info('*********** Error: %s' % e)
                                return request.make_response(
                                    json.dumps({"mensaje": "Error al actualizar el producto"}),
                                    headers={'Content-Type': 'application/json'},
                                    status=500
                                )
                        exitoso = True
                    #ORDENES
                    #order/created
                    elif webhook.event == 'order/created':
                        #Buscamos la orden en Odoo y si no existe la creamos
                        order = request.env['sale.order'].sudo().search([
                            ('id_tn','=',data['id'])
                            ],limit=1)
                        if not order:
                            #Asignamos de forma temporal como cliente a la empresa para poder crear la orden
                            order = request.env['sale.order'].sudo().create({
                                'id_tn': data['id'],
                                'partner_id': request.env.company.sudo().partner_id.id,
                                'name': 'Orden TN id: ' + str(data['id']),
                            })
                            order.sudo().create_order_from_tn()
                        exitoso = True

                if exitoso:
                    return request.make_response(
                        json.dumps({"mensaje": "Operación exitosa"}),
                        headers={'Content-Type': 'application/json'},
                        status=200
                    )
                else:
                    return request.make_response(
                        json.dumps({"mensaje": "Operación no encontrada"}),
                        headers={'Content-Type': 'application/json'},
                        status=404
                    )
        except Exception as e:
            _logger.info('*********** Error: %s' % e)
            request.env['ir.config_parameter'].sudo().set_param(lock_name, 'Disponible')
            return request.make_response(
                json.dumps({"mensaje": "Error al procesar la solicitud"}),
                headers={'Content-Type': 'application/json'},
                status=500
            )
        finally:
            request.env['ir.config_parameter'].sudo().set_param(lock_name, 'Disponible')