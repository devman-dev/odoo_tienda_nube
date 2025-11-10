import logging

from odoo import models, fields, api
_logger = logging.getLogger('GetTnLocationWizard')

class GetTnLocationWizard(models.TransientModel):
    _name = 'get.tn.location.wizard'
    _description = 'Wizard to get location from Tienda Nube'

    locations_ids = fields.One2many('get.tn.location.wizard.line', 'wizard_id', 'Ubicaciones en Tienda Nube')

    def set_location(self):
        #Eliinamos los location_id_tn actuales
        warehouse_ids = self.env['stock.warehouse'].search([('location_id_tn','!=',False)])
        warehouse_ids.location_id_tn = False
        for location in self.locations_ids:
            if location.location_id and location.warehouse_id:
                #Obtenemos solo el ID del chat location_id
                location_id = location.location_id.split('ID:')[1].strip()
                location.warehouse_id.location_id_tn = location_id
            
    def get_all_location(self):
        self.locations_ids.unlink()
        # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
        company = self.env.company if self.env.company else self.env.user.company_id
        locations = company.get_location_tn()
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
