import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class stock_move_line_inherit_tn(models.Model):
    _inherit = 'stock.move.line'

    # Write
    def write(self, vals):
        res = super(stock_move_line_inherit_tn, self).write(vals)
        _logger.info('*************** Stock move line write')
        if self.company_id.tn_config_stock_realtime:
            self.actualizar_stock_tn()
        return res

    # Create
    @api.model_create_multi
    def create(self, vals_list):
        records = super(stock_move_line_inherit_tn, self).create(vals_list)
        for rec in records:
            _logger.info('*************** company_id: {0}'.format(rec.company_id))
            _logger.info('*************** tn_config_stock_realtime: {0}'.format(rec.company_id.tn_config_stock_realtime))
            if rec.company_id.tn_config_stock_realtime:
                rec.actualizar_stock_tn()
        return records

    def actualizar_stock_tn(self):
        #Obtenemos location_id_tn del almacen de donde se hace el movimiento si no tiene no hacemos nada con TN
        location_id_tn = []
        location_id_tn.append(self.location_id.warehouse_id.location_id_tn)
        _logger.info('*************** location_id_tn: {0}'.format(location_id_tn))
        if not location_id_tn[0]:
            return

        # Actualizamos el stock en Tienda Nube
        if self.product_id.product_id_tn:
            self.company_id.update_product_stock_tn(self.product_id, location_id_tn)