import logging

from odoo import models, fields

class StockWarehouseInherit(models.Model):
    _inherit = 'stock.warehouse'

    location_id_tn = fields.Char('ID de Centros de Distribución en Tienda Nube', copy=False)