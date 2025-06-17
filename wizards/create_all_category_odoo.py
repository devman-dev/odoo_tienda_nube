from odoo import models, fields, api

class CreateAllCategoryWizard(models.TransientModel):
    _name = 'create.all.category.wizard'
    _description = 'Wizard to create all category'
    
    def create_all_category(self):
        # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
        company = self.env.company if self.env.company else self.env.user.company_id
        company.get_all_categories_tn()