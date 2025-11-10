# -*- coding: utf-8 -*-
import logging
import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CouponTn(models.Model):
    _name = 'coupon.tn'
    _description = 'Cupon Tienda Nube'

    name = fields.Char('Codigo')
    id_tn = fields.Char('ID Tienda Nube')
    type_tn = fields.Selection([
        ('percentage', 'Porcentaje'),
        ('absolute', 'Absoluto'),
        ('shipping', 'Envio Gratis'),
    ], string='Type')
    value = fields.Float('Valor')
    valid = fields.Boolean('Valido?', default=True)
    max_use = fields.Integer('Maximo de Usos', help="Maximo de Usos, 0 es ilimitado")
    includes_shipping = fields.Boolean('Include Shipping', help="Aplica para el envio?")
    start_date = fields.Date('Fecha de Inicio')
    end_date = fields.Date('Fecha de Fin')
    min_price = fields.Float('Min Price')
    used = fields.Integer('Usado', default=0)
    categoria_tn_ids = fields.Many2many('category.tn', string='Categorias Tienda Nube', help="Categorias de Tienda Nube")

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError(_('La fecha de inicio no puede ser mayor a la fecha de fin'))
    
    @api.constrains('value')
    def _check_value(self):
        for record in self:
            if record.value < 0:
                raise ValidationError(_('El valor no puede ser negativo'))
    
    @api.constrains('max_use')
    def _check_max_use(self):
        for record in self:
            if record.max_use < 0:
                raise ValidationError(_('El maximo de usos no puede ser negativo'))

    @api.constrains('min_price')
    def _check_min_price(self):
        for record in self:
            if record.min_price < 0:
                raise ValidationError(_('El precio minimo no puede ser negativo'))

    # Editamos cupon en TN PUT /coupons
    def write_coupon_tn(self):
        # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
        company = self.env.company if self.env.company else self.env.user.company_id
        url = "https://api.tiendanube.com/v1/%s/coupons/%s" % (company.tiendanube_id, self.id_tn)
        headers = company.get_headers_tn()
        category = []
        for c in self.categoria_tn_ids:
            category.append(c.tn_id)
        data = {
            "code": self.name,
            "type": self.type_tn,
            "value": str(self.value),
            "valid": self.valid,
            "max_uses": self.max_use if self.max_use > 0 else None,
            "includes_shipping": self.includes_shipping,
            "min_price": self.min_price,
            "category_id": category
        }
        if self.start_date:
            data['start_date'] = self.start_date
        if self.end_date:
            data['end_date'] = self.end_date
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            data = response.json()
            # Creamos log de TN
            self.env['tn.log'].create_log(
                name='Cupon editado en Tienda Nube con id %s' % self.id_tn,
                message=data,
                model='coupon.tn',
                model_id=self.id,
                level='success',
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Cupon editado en Tienda Nube con exito 😁',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            # Creamos log de TN
            self.env['tn.log'].create_log(
                name='Error al editar cupon',
                message=response.text,
                model='coupon.tn',
                model_id=self.id,
                level='error',
                error_tn=response.text,
            )
            self.env.cr.commit()
            raise UserError(_('Error al editar cupon en Tienda Nube, error: {0}').format(response.text))
    
    # Creamos cupon en TN POST /coupons
    def create_coupon_tn(self):
        # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
        company = self.env.company if self.env.company else self.env.user.company_id
        url = "https://api.tiendanube.com/v1/%s/coupons" % company.tiendanube_id
        headers = company.get_headers_tn()
        category = []
        for c in self.categoria_tn_ids:
            category.append(c.tn_id)
        data = {
            "code": self.name,
            "type": self.type_tn,
            "value": str(self.value),
            "valid": self.valid,
            "max_uses": self.max_use if self.max_use > 0 else None,
            "includes_shipping": self.includes_shipping,
            "min_price": self.min_price,
            "category_id": category if len(category) > 0 else None,
            "start_date": fields.Date.to_string(self.start_date) if self.start_date else None,
            "end_date": fields.Date.to_string(self.end_date) if self.end_date else None,
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            data = response.json()
            self.id_tn = data.get('id')
            # Creamos log de TN
            self.env['tn.log'].create_log(
                name='Cupon creado en Tienda Nube con id %s' % self.id_tn,
                message=data,
                model='coupon.tn',
                model_id=self.id,
                level='success',
            )
        else:
            # Creamos log de TN
            self.env['tn.log'].create_log(
                name='Error al crear cupon',
                message=response.text,
                model='coupon.tn',
                model_id=self.id,
                level='error',
                error_tn=response.text,
            )
            self.env.cr.commit()
            raise UserError(_('Error al crear cupon en Tienda Nube, error: {0}').format(response.text))

