from odoo import models, fields, api

class CreateAllOrdersWizard(models.TransientModel):
    _name = 'create.all.orders.wizard'
    _description = 'Wizard to create all orders'
    
    def create_all_orders(self):
        company = self.env.user.company_id
        company.get_all_orders_tn()