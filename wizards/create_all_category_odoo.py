from odoo import models, fields, api

class CreateAllCategoryWizard(models.TransientModel):
    _name = 'create.all.category.wizard'
    _description = 'Wizard to create all category'
    
    def create_all_category(self):
        company = self.env.user.company_id
        company.get_all_categories_tn()