import logging
import requests
from odoo.exceptions import UserError
from odoo import models, fields

_logger = logging.getLogger(__name__)

class CategoryTn(models.Model):
    _name = 'category.tn'

    name = fields.Char(string='Nombre', required=True)
    tn_id = fields.Integer(string='Tienda Nube ID')
    parent_id = fields.Many2one('category.tn', string='Categoria Padre')
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True, index=True)

    # Metodo crear o actualizar en Tienda Nube POST /categories
    def create_or_update_tn(self):
        for rec in self:
            company = rec.env.company if rec.env.company else rec.env.user.company_id
            url = "https://api.tiendanube.com/v1/%s/categories" % company.tiendanube_id
            headers = company.get_headers_tn()
            if rec.tn_id:
                method = "PUT"
                url = "%s/%s" % (url, rec.tn_id)
            else:
                method = "POST"
            data = {
                "name": rec.name,
                "parent": rec.parent_id.tn_id if rec.parent_id else None
            }
            response = requests.request(method, url, headers=headers, json=data)

            if response.status_code == 201:
                response_data = response.json()
                rec.tn_id = response_data['id']
            elif response.status_code == 200:
                pass
            else:
                raise UserError("Error al sincronizar con Tienda Nube") 

    # Metodo editar en Odoo desde Tienda Nube GET /categories/{id}
    def update_category_tn_odoo(self):
        for rec in self:
            if not rec.tn_id:
                raise UserError("No se puede actualizar una categoria sin ID de Tienda Nube")
            if self.env.context.get('company_id'):
                company = self.env['res.company'].browse(self.env.context.get('company_id'))
            else:
                company = rec.env.company if rec.env.company else rec.env.user.company_id
            url = "https://api.tiendanube.com/v1/%s/categories/%s" % (company.tiendanube_id, rec.tn_id)
            headers = company.get_headers_tn()
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                rec.name = response_data['name']['es']
                parent = False
                if response_data['parent'] != 0:
                    parent = rec.search([('tn_id', '=', response_data['parent'])], limit=1)
                rec.parent_id = parent
            else:
                raise UserError("Error al sincronizar con Tienda Nube")


