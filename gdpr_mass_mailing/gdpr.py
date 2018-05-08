# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP,  Open Source Management Solution,  third party addon
#    Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation,  either version 3 of the
#    License,  or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not,  see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models,  fields,  api,  _, http
from datetime import timedelta

from openerp.addons.mass_mailing.controllers.main import MassMailController
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)

# https://www.privacy-regulation.eu
class MailMassMailingList(models.Model):
    _inherit = 'mail.mass_mailing.list'

    #consent_ids = fields.One2many(string='Recipients', comodel_name='gdpr.consent')
    gdpr_id = fields.Many2one(string='GDPR Inventory', comodel_name='gdpr.inventory')

class MailMassMailing(models.Model):
    _inherit = 'mail.mass_mailing'

    gdpr_id = fields.Many2one(string='GDPR Inventory', comodel_name='gdpr.inventory')
    gdpr_domain = fields.Text(string='GDPR Object IDs', compute='get_gdpr_domain')
    gdpr_consent = fields.Selection(selection=[('given', 'Given'), ('withdrawn', 'Withdrawn'), ('missing', 'Missing')], string='Consent State')
    recipients = fields.Integer(readonly=True)

    @api.onchange('gdpr_id', 'gdpr_consent')
    def get_gdpr_domain(self):
        domain = []
        if self.gdpr_id:
            if self.gdpr_id.lawsection_id.consent:
                if self.gdpr_consent in ['given', 'withdrawn']:
                    object_ids = [d['gdpr_object_id'][0] for d in self.env['gdpr.consent'].search_read([('state', '=', self.gdpr_consent), ('gdpr_id', '=', self.gdpr_id.id)], ['gdpr_object_id'])]
                else:
                    object_ids = (self.gdpr_id.object_ids - self.env['gdpr.consent'].search([('gdpr_id', '=', self.gdpr_id.id)]).mapped('gdpr_object_id')).mapped('id')
                # ~ _logger.warn(self.env['gdpr.object'].search_read([('id', 'in', object_ids), ('restricted', '=', False)], ['object_res_id']))
                # ~ object_ids = [d['object_res_id'] for d in self.env['gdpr.object'].search_read([('id', 'in', object_ids), ('restricted', '=', False)], ['object_res_id'])]
            else:
                object_ids = [d['object_res_id'] for d in self.env['gdpr.object'].search_read([('gdpr_id', '=', self.gdpr_id.id), ('restricted', '=', False)], ['object_res_id'])]
            domain = [('id', 'in', object_ids)]
            self.recipients = len(object_ids)
        self.gdpr_domain = domain


class GDPRMailMassMailingList(models.Model):
    _name = 'gdpr.mail.mass_mailing.list'

    name = fields.Char(string='name', required=True)
    gdpr_ids = fields.Many2many(comodel_name='gdpr.inventory', string='GDPRs')
    gdpr_consent = fields.Selection(selection=[('given', 'Given'), ('withdrawn', 'Withdrawn'), ('missing', 'Missing')], string='Consent State')
    contact_nbr = fields.Integer(compute='_get_contact_nbr', string='Number of Contacts')
    _mail_mass_mailing = _('Sale Order')
    @api.one
    def _get_contact_nbr(self):
        contact_nbr = len(self.env['gdpr.mail.mass_mailing.contact'].search([('list_id', '=', self.id)]))


class GDPRMassMailingContact(models.Model):
    _name = 'gdpr.mail.mass_mailing.contact'
    _inherit = 'mail.thread'

    name = fields.Char(string='Name')
    email = fields.Char(string='Email', required=True)
    create_date = fields.Datetime(string='Create Date')
    list_id = fields.Many2one(comodel_name='gdpr.mail.mass_mailing.list', string='Mailing List', ondelete='cascade', required=True)
    opt_out = fields.Boolean(string='Opt Out', help='The contact has chosen not to receive mails anymore from this list')


class MassMailController(MassMailController):

    @http.route(['/mail/mailing/<int:mailing_id>/unsubscribe'], type='http', auth='none')
    def mailing(self, mailing_id, email=None, res_id=None, **post):
        res = super(MassMailController, self).mailing(mailing_id, email, res_id, **post)
        if res.get_data() == 'OK':
            mailing = request.env['mail.mass_mailing'].sudo().browse(mailing_id)
            if mailing.mailing_model == 'mail.mass_mailing.contact':
                list_ids = [l.id for l in mailing.contact_list_ids]
                records = request.env[mailing.mailing_model].sudo().search([('list_id', 'in', list_ids), ('id', '=', res_id), ('email', 'ilike', email)])
                consent = request.env['gdpr.consent'].sudo().search([('gdpr_object_id.record_id', '=', '%s,%s' % (mailing.mailing_model, records.id))])
                if consent:
                    consent.remove("User unsubscribed through %s (referer: %s)" % (request.httprequest.path, request.httprequest.referrer))
            elif mailing.gdpr_id and res_id:
                consent = request.env['gdpr.consent'].sudo().search([
                    ('record_id', '=', '%s,%s' % (mailing.mailing_model, res_id)),
                    ('partner_id.email', '=', email),
                    ('gdpr_id', '=', mailing.gdpr_id.id)])
                if consent:
                    consent.remove("User unsubscribed through %s (referer: %s)" % (request.httprequest.path, request.httprequest.referrer))
        return res
