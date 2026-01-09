import logging

from odoo import models,  fields,  api,  _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    """
    1) search for non inventoried res.partner
    2) button: consents
    3) button: list related gdpr.inventorie (other law sections)
    4) for each gdpr.inventory list document related to res.partner and gdpr.inventory
    5) list res.partber for each gdpr.inventory

    """
    def _gdpr_ids(self):
        self.ensure_one()
        self.gdpr_ids = self.env['gdpr.object'].search([('partner_id', '=', self.id)]).mapped('gdpr_id')
    gdpr_ids = fields.Many2many(string='GDPRs', comodel_name='gdpr.inventory', compute='_gdpr_ids')
    def _get_gdpr_count(self):
        self.ensure_one()
        self.gdpr_count = len(self.gdpr_ids)
    gdpr_count = fields.Integer(string='# Inventories', compute='_get_gdpr_count')

    consent_ids = fields.One2many(string='Consents', comodel_name='gdpr.consent', inverse_name='partner_id')
    def _get_consent_count(self):
        self.ensure_one()
        self.consent_count = len(self.consent_ids)
    consent_count = fields.Integer(string='# Consents', compute='_get_consent_count')

    gdpr_object_ids = fields.One2many(comodel_name='gdpr.object', inverse_name='partner_id', string='GDPR Objects')
    def _get_gdpr_object_count(self):
        self.ensure_one()
        self.gdpr_object_count = len(self.gdpr_object_ids)
    gdpr_object_count = fields.Integer(string='# Objects', compute='_get_gdpr_object_count')

    
    def action_gdpr_inventory(self):
        action = self.env['ir.actions.act_window'].for_xml_id('gdpr_inventory', 'action_gdpr_inventory')
        action['domain'] = [('partner_ids', '=', self.id)]
        return action

    
    def action_gdpr_objects(self):
        action = self.env['ir.actions.act_window'].for_xml_id('gdpr_inventory', 'action_gdpr_object')
        action['domain'] = [('partner_ids', '=', self.id)]
        return action

    
    def act_res_partner_2_gdpr_inventory(self):
        return {
            'name': 'Res Partner 2 GDPR Inventory',
            'res_model': 'gdpr.inventory',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,list,form',
            'view_type': 'kanban',
            'domain': [('id', 'in', self.gdpr_ids.mapped('id'))],
            'context': {},
        }

    """
    write: if gdpr.gdpr_method_id.type in (encrypt)
    read: decrypt fields
    """