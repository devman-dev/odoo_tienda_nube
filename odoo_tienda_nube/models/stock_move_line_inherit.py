import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class stock_move_line_inherit_tn(models.Model):
    _inherit = 'stock.move.line'

    # Write
    def write(self, vals):
        res = super(stock_move_line_inherit_tn, self).write(vals)
        if self.company_id.tn_config_stock_realtime:
            self.actualizar_stock_tn()
        return res

    # Create
    @api.model_create_multi
    def create(self, vals_list):
        records = super(stock_move_line_inherit_tn, self).create(vals_list)
        for rec in records:
            if rec.company_id.tn_config_stock_realtime:
                rec.actualizar_stock_tn()
        return records

    def actualizar_stock_tn(self):
        for rec in self:
            #Obtenemos location_id_tn del almacen de donde se hace el movimiento si no tiene no hacemos nada con TN
            location_id_tn = []
            location_id_tn.append(rec.location_id.warehouse_id.location_id_tn)
            if not location_id_tn[0]:
                return
    
            # Actualizamos el stock en Tienda Nube
            if rec.product_id.product_id_tn:
                rec.company_id.update_product_stock_tn(rec.product_id, location_id_tn)
