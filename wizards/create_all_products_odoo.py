from odoo import models, fields, api

class CreateAllProductsWizard(models.TransientModel):
    _name = 'create.all.products.wizard'
    _description = 'Wizard to create all products'
    
    def create_all_products(self):
        company = self.env.user.company_id
        company.create_products_in_odoo()