from odoo import models, fields, api

class CreateAllWebhookWizard(models.TransientModel):
    _name = 'create.all.webhook.wizard'
    _description = 'Wizard to create all webhook'
    
    def create_all_webhook(self):
        company = self.env.user.company_id
        company.get_webhooks_tn()