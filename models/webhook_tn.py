import logging
import requests
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class WebhookTN(models.Model):
    _name = 'webhook.tn'
    _description = 'Tienda Nube Webhook'

    name = fields.Char(string='Name', required=True)
    id_webhook_tn = fields.Char(string='ID Tienda Nube')
    url = fields.Char(string='URL', required=True, help='URL del webhook en Tienda Nube')
    event = fields.Selection([
        ('category/created', 'Categoria creada'),
        ('category/updated', 'Categoria actualizada'),
        ('category/deleted', 'Categoria eliminada'),
        ('order/created', 'Orden creada'),
        ('order/updated', 'Orden actualizada'),
        ('order/edited', 'Orden editada'),
        ('order/paid', 'Orden pagada'),
        ('order/cancelled', 'Orden cancelada'),
        ('order/fulfilled', 'Orden completada'),
        ('order/packed', 'Orden empaquetada'),
        ('product/created', 'Producto creado'),
        ('product/updated', 'Producto actualizado'),
        ('product/deleted', 'Producto eliminado'),
    ], string='Evento', required=True)
    created_at_tn = fields.Datetime(string='Fecha de creación en Tienda Nube')
    updated_at_tn = fields.Datetime(string='Fecha de actualización en Tienda Nube')

    # Validamos en el wirte y create que la url inicie de forma correcta siendo la url de odoo que figura en paramentros de sistema continuando con /webhook_tn
    @api.model
    def create(self, vals):
        if vals.get('url') and not vals.get('url').startswith(self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/webhook_tn'):
            raise ValidationError('La URL debe iniciar con %s/webhook_tn/' % self.env['ir.config_parameter'].sudo().get_param('web.base.url'))
        return super(WebhookTN, self).create(vals)

    def write(self, vals):
        if vals.get('url') and not vals.get('url').startswith(self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/webhook_tn'):
            raise ValidationError('La URL debe iniciar con %s/webhook_tn/' % self.env['ir.config_parameter'].sudo().get_param('web.base.url'))
        return super(WebhookTN, self).write(vals)


    # Metodo para eliminar el webhook en Tienda Nube DELETE /webhooks/{id}
    def delete_webhook_tn(self):
        company = self.env.user.company_id
        url = "https://api.tiendanube.com/v1/%s/webhooks/%s" % (company.tiendanube_id, self.id_webhook_tn)
        headers = company.get_headers_tn()
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            self.id_webhook_tn = False
        else:
            raise ValidationError('Error al eliminar el webhook en Tienda Nube, error: %s' % response.text)

    # Metodo para crear o editar el webhook en Tienda Nube POST /webhooks y PUT /webhooks/{id}
    def create_or_update_webhook_tn(self):
        company = self.env.user.company_id
        url = "https://api.tiendanube.com/v1/%s/webhooks" % company.tiendanube_id
        headers = company.get_headers_tn()
        payload = {
            "id": self.id,
            "store_id": int(company.tiendanube_id),
            "event": self.event,
            "url": self.url,
        }
        if self.id_webhook_tn:
            url = "%s/%s" % (url, self.id_webhook_tn)
            response = requests.put(url, headers=headers, json=payload)
            if response.status_code == 200:
                return True
            else:
                raise ValidationError('Error al actualizar el webhook en Tienda Nube, error: %s' % response.text)
        else:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 201:
                data = response.json()
                self.id_webhook_tn = data.get('id')
                self.created_at_tn = datetime.datetime.strptime(data.get('created_at'), '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
                self.updated_at_tn = datetime.datetime.strptime(data.get('updated_at'), '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
                return True
            raise ValidationError('Error al actualizar el webhook en Tienda Nube, error: %s' % response.text)

class WebhookTNReceived(models.Model):
    _name = 'webhook.tn.received'
    _description = 'Webhook Recibido'
    _order = 'create_date desc'

    name = fields.Char(string='Name', required=True)
    id_event_tn = fields.Char(string='ID Tienda Nube')
    event = fields.Selection([
        ('category/created', 'Categoria creada'),
        ('category/updated', 'Categoria actualizada'),
        ('category/deleted', 'Categoria eliminada'),
        ('order/created', 'Orden creada'),
        ('order/updated', 'Orden actualizada'),
        ('order/edited', 'Orden editada'),
        ('order/paid', 'Orden paganada'),
        ('order/cancelled', 'Orden cancelada'),
        ('order/fulfilled', 'Orden completada'),
        ('order/packed', 'Orden empaquetada'),
        ('product/created', 'Producto creado'),
        ('product/updated', 'Producto actualizado'),
        ('product/deleted', 'Producto eliminado'),
    ], string='Evento', required=True)
    store_id = fields.Char(string='ID Tienda Nube')

        