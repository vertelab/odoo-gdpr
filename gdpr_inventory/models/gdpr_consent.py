import logging

from odoo import models,  fields,  api,  _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

class gdpr_consent(models.Model):
    """
    1. Where processing is based on consent,  the controller shall be able to demonstrate that the data subject has consented to processing of his or her personal data.
    2. If the data subject's consent is given in the context of a written declaration which also concerns other matters,  the request for consent shall be presented in a manner which is clearly distinguishable from the other matters,  in an intelligible and easily accessible form,  using clear and plain language. Any part of such a declaration which constitutes an infringement of this Regulation shall not be binding.
    3. The data subject shall have the right to withdraw his or her consent at any time. The withdrawal of consent shall not affect the lawfulness of processing based on consent before its withdrawal. Prior to giving consent,  the data subject shall be informed thereof. It shall be as easy to withdraw as to give consent.
    4. When assessing whether consent is freely given,  utmost account shall be taken of whether,  inter alia,  the performance of a contract,  including the provision of a service,  is conditional on consent to the processing of personal data that is not necessary for the performance of that contract.
    """
    _name = 'gdpr.consent'
    _description = "Given consents"
    _inherit = ['mail.thread']

    name = fields.Char(string='Name')
    gdpr_object_id = fields.Many2one(comodel_name='gdpr.object', string='GDPR Object')
    record_id = fields.Reference(related='gdpr_object_id.object_id', string="Object", help="Object that is consented for processing of personal data")
    partner_id = fields.Many2one(comodel_name="res.partner")
    gdpr_id = fields.Many2one(comodel_name='gdpr.inventory', help="Description of consent")
    date = fields.Date(string="Date", help="Date when consent first given")
    state = fields.Selection(selection=[('given', 'Given'), ('withdrawn', 'Withdrawn'), ('missing', 'Missing')], string="State", track_visibility='onchange') # transaction log

    def remove(self, msg):
        self.ensure_one()
        self.state = 'withdrawn'
        self.env['mail.message'].create({
            'body': msg.replace('\n', '<BR/>'),
            'subject': 'Consent withdrawn',
            'author_id': self.env.user.partner_id.id,
            'res_id': self.id,
            'model': self._name,
            'type': 'notification',})

    @api.model
    def add(self, gdpr_id, object, email=None, partner=None, name=None, msg=''):
        partner = partner or self.env['res.partner'].search([('email', '=', email)], limit=1)
        if email and not partner:
            partner = self.env['res.partner'].sudo().create({'name': name or email, 'email': email})
        if object._name != 'gdpr.object':
            object_id = self.env['gdpr.object'].sudo().search([
                ('gdpr_id', '=', gdpr_id.id),
                ('object_id', '=', '%s,%s' %(object._name, object.id)),
                ('partner_id', '=', partner.id),
            ])
            if not object_id:
                object_id = self.env['gdpr.object'].sudo().create({
                    'gdpr_id': gdpr_id.id,
                    'object_id': '%s,%s' %(object._name, object.id),
                    'partner_id': partner.id,
                })
        else:
            object_id = object
        consent = self.get_consent(gdpr_id, partner, object_id)
        if not consent:
            consent = self.env['gdpr.consent'].sudo().create({
                'name': _('Consent %s') %partner.name,
                'gdpr_id': gdpr_id.id,
                'partner_id': partner.id,
                'gdpr_object_id': object_id.id,
            })
        consent.state = 'given'
        self.env['mail.message'].create({
            'body': msg.replace('\n', '<BR/>'),
            'subject': 'Consent given',
            'author_id': self.env.user.partner_id.id,
            'res_id': consent.id,
            'model': consent._name,
            'type': 'notification',})
        return consent

    @api.model
    def get_consent(self, gdpr_id, partner_id, object_id):
        if object_id._name != 'gdpr.object':
            object_id = self.env['gdpr.object'].sudo().search([('gdpr_id', '=', gdpr_id.id), ('partner_id', '=', partner_id.id), ('object_id', '=', '%s,%s' % (object_id._name, object_id.id))], limit=1)
        return self.env['gdpr.consent'].sudo().search([('gdpr_id', '=', gdpr_id.id), ('partner_id', '=', partner_id.id), ('gdpr_object_id', '=', object_id.id)], limit=1)
