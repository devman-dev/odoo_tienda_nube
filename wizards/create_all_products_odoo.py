from odoo import models, fields, api

class CreateAllProductsWizard(models.TransientModel):
    _name = 'create.all.products.wizard'
    _description = 'Wizard to create all products'
    
    def create_all_products(self):
        # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
        company = self.env.company if self.env.company else self.env.user.company_id
        company.create_products_in_odoo()