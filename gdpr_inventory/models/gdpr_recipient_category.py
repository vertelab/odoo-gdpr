from odoo import models, fields


class gdpr_recipient_category(models.Model):
    _name = 'gdpr.recipient_category'
    _description = 'GDPR Recipient Category'
    _order = 'sequence, name'

    sequence = fields.Integer(string='Sequence')
    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(string='Active', default=True)
    inventory_ids = fields.Many2many(comodel_name='gdpr.inventory', string='Inventories')
