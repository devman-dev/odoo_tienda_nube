from odoo import models, fields, api

class CreateAllCouponWizard(models.TransientModel):
    _name = 'create.all.coupon.wizard'
    _description = 'Wizard to create all coupon'
    
    def create_all_coupon(self):
        company = self.env.user.company_id
        company.get_all_coupon_tn()
        # Recargamos pagina para que se visualicen los cambios
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }