# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class TnLog(models.Model):
    _name = 'tn.log'
    _description = 'Tienda Nube Log'
    _order = 'date desc'

    name = fields.Char('Name')
    date = fields.Datetime('Date', default=fields.Datetime.now)
    message = fields.Text('Message')
    model = fields.Char('Model')
    model_id = fields.Integer('Model ID')
    level = fields.Selection([
        ('success', 'Hecho'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], string='Level', default='info')
    error_tn = fields.Text('Error Tienda Nube')

    @api.model
    def create_log(self, name, message, model, model_id, level='info', error_tn=False):
        self.create({
            'name': name,
            'message': message,
            'model': model,
            'model_id': model_id,
            'level': level,
            'error_tn': error_tn,
        })
        
    def mark_as_solved(self):
        for rec in self:
            rec.write({'level': 'success'})