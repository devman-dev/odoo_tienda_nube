from odoo import models, fields, api

class CreateAllOrdersWizard(models.TransientModel):
    _name = 'create.all.orders.wizard'
    _description = 'Wizard to create all orders'
    
    def create_all_orders(self):
        # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
        company = self.env.company if self.env.company else self.env.user.company_id
        company.get_all_orders_tn()