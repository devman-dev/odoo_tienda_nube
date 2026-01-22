from odoo import models, fields, api

class CreateAllWebhookWizard(models.TransientModel):
    _name = 'create.all.webhook.wizard'
    _description = 'Wizard to create all webhook'
    
    def create_all_webhook(self):
        # NOTE: Utilizamos la compañia que tiene seleccionada el usuario actual o en caso contrario la compañia predeterminada de ese usuario
        company = self.env.company if self.env.company else self.env.user.company_id
        company.get_webhooks_tn()