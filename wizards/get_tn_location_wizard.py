import logging

from odoo import models, fields, api
_logger = logging.getLogger('GetTnLocationWizard')

class GetTnLocationWizard(models.TransientModel):
    _name = 'get.tn.location.wizard'
    _description = 'Wizard to get location from Tienda Nube'

    locations_ids = fields.One2many('get.tn.location.wizard.line', 'wizard_id', 'Ubicaciones en Tienda Nube')

    def set_location(self):
        for location in self.locations_ids:
            if location.location_id and location.warehouse_id:
                #Obtenemos solo el ID del chat location_id
                location_id = location.location_id.split('ID:')[1].strip()
                location.warehouse_id.location_id_tn = location_id
            
    def get_all_location(self):
        self.locations_ids.unlink()
        company = self.env.user.company_id
        locations = company.get_location_tn()
        _logger.warning(locations)
        for location in locations:
            self.locations_ids.create({'wizard_id': self.id, 'location_id': location['name']['es_AR'] + ' | ' + location['address']['city'] + ' | ID:' + location['id']})

        
        # Retorna una acción de recarga para mantener el wizard abierto
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

class GetTnLocationWizardLine(models.TransientModel):
    _name = 'get.tn.location.wizard.line'

    wizard_id = fields.Many2one('get.tn.location.wizard', 'Wizard')
    location_id = fields.Char('ID de Almancen en Tienda Nube', help="ID de Almancen en Tienda Nube", copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen')
