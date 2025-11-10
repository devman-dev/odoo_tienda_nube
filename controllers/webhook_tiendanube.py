# -*- coding: utf-8 -*-
import logging

import odoo
import json
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)
CORS = '*'

class TiendaNubeWebHook(http.Controller):

    # https://tiendanube.github.io/api-documentation/resources/webhook#rules-for-deduplication
    # verificamos segun 3 segundos de diferencia en creacion del ultimo webhook igual
    def duplicity_check(self, data):
        webhook_received = request.env['webhook.tn.received'].sudo().search([
            ('id_event_tn','=',data['id']),('event','=',data['event']),('store_id','=',data['store_id'])
            ],limit=1, order='create_date desc')
        if webhook_received and (odoo.fields.Datetime.now() - webhook_received.create_date).seconds < 3:
            return True
        return False

    #Controller para descargar adjuntos
    @http.route('/webhook_tn/<string:code_event>', auth='public', cors=CORS, csrf=False)
    def TiendaNubeWebHook(self, **kw):

        
        # Verificación de locking
        lock_name = 'webhook_processing'
        if request.env['ir.config_parameter'].sudo().get_param(lock_name) == 'En uso':
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

            if 'code_event' in kw:
                code_event = kw['code_event']
                webhook = request.env['webhook.tn'].sudo().search([
                    ('url','=',request.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/webhook_tn/' + code_event)
                    ],limit=1)
                exitoso = False

                # Recordset de empresa para pasar la empresa en el contexto de creaciones
                company_id = webhook.company_id if webhook.company_id else None
                if webhook:
                    #CATEGORIAS
                    #category/updated
                    if webhook.event == 'category/updated':
                        category = request.env['category.tn'].sudo().search([
                            ('tn_id','=',data['id'])
                            ],limit=1)
                        if category:
                            category.sudo().with_company(company_id).update_category_tn_odoo()
                        exitoso = True
                        
                    #category/created
                    elif webhook.event == 'category/created':
                        #Creamos la/s categoria/s nueva/s
                        webhook.company_id.sudo().get_all_categories_tn()
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
                                product = request.env['product.template'].with_company(company_id).sudo().create({
                                    'id_tn': data['id'],
                                    'name': 'Nuevo Producto TN id: ' + str(data['id']),
                                })
                            product.sudo().with_company(company_id).create_update_product_from_tn()
                            exitoso = True
                        except Exception as e:
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
                                product.sudo().with_company(company_id).create_update_product_from_tn()
                            except Exception as e:
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
                            order = request.env['sale.order'].with_company(company_id).sudo().create({
                                'id_tn': data['id'],
                                'partner_id': request.env.company.sudo().partner_id.id,
                                'name': 'Orden TN id: ' + str(data['id']),
                            })
                            order.sudo().with_company(company_id).create_order_from_tn()
                        exitoso = True

                    #order/paid
                    elif webhook.event == 'order/paid':
                        #Buscamos la orden en Odoo y si no existe la creamos
                        order = request.env['sale.order'].sudo().search([
                            ('id_tn','=',data['id'])
                            ],limit=1)
                        if not order:
                            #Asignamos de forma temporal como cliente a la empresa para poder crear la orden
                            order = request.env['sale.order'].with_company(company_id).sudo().create({
                                'id_tn': data['id'],
                                'partner_id': request.env.company.sudo().partner_id.id,
                                'name': 'Orden TN id: ' + str(data['id']),
                            })
                            order.sudo().with_company(company_id).create_order_from_tn()
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
            request.env['ir.config_parameter'].sudo().set_param(lock_name, 'Disponible')
            return request.make_response(
                json.dumps({"mensaje": "Error al procesar la solicitud"}),
                headers={'Content-Type': 'application/json'},
                status=500
            )
        finally:
            request.env['ir.config_parameter'].sudo().set_param(lock_name, 'Disponible')
