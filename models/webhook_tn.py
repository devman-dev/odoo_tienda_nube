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
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company if self.env.company else self.env.user.company_id, required=True)
    id_webhook_tn = fields.Char(string='ID Tienda Nube')
    url = fields.Char(string='URL', required=True, help='URL del webhook en Tienda Nube')
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
    created_at_tn = fields.Datetime(string='Fecha de creación en Tienda Nube')
    updated_at_tn = fields.Datetime(string='Fecha de actualización en Tienda Nube')

    # Validamos en el wirte y create que la url inicie de forma correcta siendo la url de odoo que figura en paramentros de sistema continuando con /webhook_tn
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            url_base = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            webhook_base_url = url_base + '/webhook_tn/'
            if vals.get('url') and not vals.get('url').startswith(webhook_base_url):
                raise ValidationError('La URL debe iniciar con %s/webhook_tn/' % url_base)
            elif vals.get('url') == webhook_base_url:
                raise ValidationError('La URL no puede ser la misma que la de Odoo + /webhook_tn/, debe ser de esta manera mas algo por ejemplo: %s/webhook_tn/mi_webhook' % url_base)
        return super(WebhookTN, self).create(vals_list)

    def write(self, vals):
        if vals.get('url') and not vals.get('url').startswith(self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/webhook_tn/'):
            raise ValidationError('La URL debe iniciar con %s/webhook_tn/' % self.env['ir.config_parameter'].sudo().get_param('web.base.url'))
        elif vals.get('url') == self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/webhook_tn/':
            raise ValidationError('La URL no puede ser la misma que la de Odoo + /webhook_tn, debe ser de esta manera mas algo por ejemplo: %s/webhook_tn/mi_webhook' % self.env['ir.config_parameter'].sudo().get_param('web.base.url'))
        return super(WebhookTN, self).write(vals)


    # Metodo para eliminar el webhook en Tienda Nube DELETE /webhooks/{id}
    def delete_webhook_tn(self):
        # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
        company = self.env.company if self.env.company else self.env.user.company_id
        url = "https://api.tiendanube.com/v1/%s/webhooks/%s" % (company.tiendanube_id, self.id_webhook_tn)
        headers = company.get_headers_tn()
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            self.id_webhook_tn = False
        else:
            raise ValidationError('Error al eliminar el webhook en Tienda Nube, error: %s' % response.text)

    # Metodo para crear o editar el webhook en Tienda Nube POST /webhooks y PUT /webhooks/{id}
    def create_or_update_webhook_tn(self):
        # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
        company = self.env.company if self.env.company else self.env.user.company_id
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
        ('order/paid', 'Orden pagada'),
        ('order/cancelled', 'Orden cancelada'),
        ('order/fulfilled', 'Orden completada'),
        ('order/packed', 'Orden empaquetada'),
        ('product/created', 'Producto creado'),
        ('product/updated', 'Producto actualizado'),
        ('product/deleted', 'Producto eliminado'),
    ], string='Evento', required=True)
    store_id = fields.Char(string='ID Tienda Nube')

        