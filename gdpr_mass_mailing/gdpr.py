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
    gdpr_lawsection_consent = fields.Boolean(related='gdpr_id.lawsection_id.consent')
    recipients = fields.Integer(readonly=True)
    gdpr_mailing_list_ids = fields.Many2many(comodel_name='gdpr.mail.mass_mailing.list', string='GDPR Mailing Lists')
    gdpr_consent_collected = fields.Many2many(string='Collected GDPR Inventory', comodel_name='gdpr.inventory')
    wp_cond_consent_ids = fields.Many2many(comodel_name='gdpr.inventory', string='Conditional', relation='mail_mass_mailing_gdpr_inventory_cond_rel', column1='mailing_id', column2='gdpr_id', help='Conditional Consents for Web Page', domain="[('lawsection_id.consent', '=', True)]")
    wp_uncond_consent_ids = fields.Many2many(comodel_name='gdpr.inventory', string='Unconditional', relation='mail_mass_mailing_gdpr_inventory_uncond_rel', column1='mailing_id', column2='gdpr_id', help='Unconditional Consents for Web Page', domain="[('lawsection_id.consent', '=', True)]")
    wp_consent_url = fields.Char(string='Web Page URL', default='$website_consent', help='URL for give consent.')
    wp_mailing_title = fields.Char(string='Web Page Title')
    wp_mailing_txt = fields.Html(string='Web Page Text')
    # ~ def _wp_mailing_url(self):
        # ~ self.wp_mailing_url = '<a class="btn btn-default" href="%s/mail/consent/%s/partner/${object.partner_id.id}">%s</a>' %(self.env['ir.config_parameter'].get_param('web.base.url'), self.id, _('Give Consents'))
    # ~ wp_mailing_url = fields.Char(string='Web Page URL', compute='_wp_mailing_url')

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

    @api.onchange('mailing_model', 'gdpr_mailing_list_ids')
    def on_change_gdpr_model_and_list(self):
        consents = self.env['gdpr.consent'].browse()
        partners = set()
        for lst in self.gdpr_mailing_list_ids:
            for consent_ids in lst.mapped('gdpr_ids').mapped('consent_ids'):
                consents |= consent_ids.filtered(lambda c: c.state == lst.gdpr_consent and c.partner_id.id not in partners)
                partners = partners.union(set(consents.mapped('partner_id').mapped('id')))
        if len(consents) > 0:
            self.mailing_domain = "[('id', 'in', %s)]" %consents.mapped('id')

    @api.model
    def get_recipients(self, mailing):
        if mailing.mailing_model == 'gdpr.consent':
            consents = self.env['gdpr.consent'].browse()
            partners = set()
            for lst in mailing.gdpr_mailing_list_ids:
                for consent_ids in lst.mapped('gdpr_ids').mapped('consent_ids'):
                    consents |= consent_ids.filtered(lambda c: c.state == lst.gdpr_consent and c.partner_id.id not in partners)
                    partners = partners.union(set(consents.mapped('partner_id').mapped('id')))
            return consents.mapped('id')
        else:
            return super(MailMassMailing, self).get_recipients(mailing)


class GDPRMailMassMailingList(models.Model):
    _name = 'gdpr.mail.mass_mailing.list'

    name = fields.Char(string='name', required=True)
    gdpr_ids = fields.Many2many(comodel_name='gdpr.inventory', string='GDPRs')
    gdpr_consent = fields.Selection(selection=[('given', 'Given'), ('withdrawn', 'Withdrawn'), ('missing', 'Missing')], string='Consent State')
    consent_nbr = fields.Integer(compute='_get_consent_nbr', string='Number of Contacts')

    @api.one
    def _get_consent_nbr(self):
        self.consent_nbr = len(self.env['gdpr.consent'].search([('gdpr_id', 'in', self.gdpr_ids.mapped('id')), ('state', '=', self.gdpr_consent)]))

    @api.model
    def get_consents(self, mailing):
        consents = self.env['gdpr.consent'].browse()
        # TODO: handle missing consents
        for inventory in mailing.gdpr_ids:
            consents |= inventory.consent_ids.filtered(lambda c: c.state == mailing.gdpr_consent)
        return consents

    @api.one
    def create_missing_consents(self):
        for inventory in self.gdpr_ids:
            for partner in inventory.partner_ids:
                if not partner.consent_ids.filtered(lambda c: c.gdpr_id == inventory):
                    self.env['gdpr.consent'].create({
                        'name': '%s - %s' %(inventory.name, partner.name),
                        'record_id': '%s,%s' %(partner._name, partner.id),
                        'partner_id': partner.id,
                        'gdpr_id': inventory.id,
                        'state': self.gdpr_consent,
                    })

    @api.multi
    def show_consents(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gdpr.consent',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('gdpr_inventory.view_gdpr_consent_tree').id,
            'target': 'current',
            'domain': [('id', 'in', self.get_consents(self).mapped('id'))],
            'context': {},
        }


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def send_get_mail_body(self, mail, partner=None):
        """ Override to add the full website version URL to the body. """
        body = super(MailMail, self).send_get_mail_body(mail, partner=partner)
        if mail.model == 'gdpr.consent':
            return body.replace('$website_consent', _('<a href="%s/mail/consent/%s/partner/%s">Give Consents</a>') %(self.env['ir.config_parameter'].get_param('web.base.url'), mail.mailing_id.id, partner.id))
        else:
            return body


class gdpr_consent(models.Model):
    _inherit = 'gdpr.consent'

    _mail_mass_mailing = _('GDPR Consents')


class MassMailController(MassMailController):

    @http.route(['/mail/mailing/<int:mailing_id>/unsubscribe'], type='http', auth='public', website=True)
    def mailing(self, mailing_id, email=None, res_id=None, **post):
        res = super(MassMailController, self).mailing(mailing_id, email, res_id, **post)
        if res.get_data() == 'OK':
            mailing = request.env['mail.mass_mailing'].sudo().browse(mailing_id)
            if mailing.mailing_model == 'mail.mass_mailing.contact':
                list_ids = [l.id for l in mailing.contact_list_ids]
                records = request.env[mailing.mailing_model].sudo().search([('list_id', 'in', list_ids), ('id', '=', res_id), ('email', 'ilike', email)])
                consent = request.env['gdpr.consent'].sudo().search([('record_id', '=', '%s,%s' % (mailing.mailing_model, records.id))])
                if consent:
                    consent.sudo().remove("User unsubscribed through %s (referer: %s)" % (request.httprequest.path, request.httprequest.referrer))
            elif mailing.mailing_model == 'gdpr.consent' and res_id:
                consent = request.env['gdpr.consent'].sudo().browse(int(res_id))
                consent.remove("User unsubscribed through %s (referer: %s)" % (request.httprequest.path, request.httprequest.referrer))
            elif mailing.gdpr_id and res_id:
                consent = request.env['gdpr.consent'].sudo().search([
                    ('record_id', '=', '%s,%s' % (mailing.mailing_model, res_id)),
                    ('partner_id.email', '=', email),
                    ('gdpr_id', '=', mailing.gdpr_id.id)])
                if consent:
                    consent.sudo().remove("User unsubscribed through %s (referer: %s)" % (request.httprequest.path, request.httprequest.referrer))
                else:
                    consent = request.env['gdpr.consent'].sudo().create([
                    ('record_id', '=', '%s,%s' % (mailing.mailing_model, res_id)),
                    ('partner_id.email', '=', email),
                    ('gdpr_id', '=', mailing.gdpr_id.id),
                    ('state', '=', 'withdrawn')])
        return request.website.render('gdpr_mass_mailing.consent_thanks', {'inventory': mailing.gdpr_id if mailing.gdpr_id else consent.gdpr_id, 'confirm': 0})

    @http.route(['/mail/consent/<int:mailing_id>/partner/<int:partner_id>'], type='http', auth='public', website=True)
    def mailing_consents(self, mailing_id, partner_id, **post):
        mailing = request.env['mail.mass_mailing'].sudo().browse(mailing_id)
        partner = request.env['res.partner'].sudo().browse(partner_id)
        if mailing and partner:
            cond_consent_inventories = mailing.wp_cond_consent_ids
            uncond_consent_inventories = mailing.wp_uncond_consent_ids
            if mailing and partner:
                return request.website.render('gdpr_mass_mailing.mailing_consents', {
                    'mailing': mailing,
                    'partner': partner,
                    'consent_inventories': cond_consent_inventories + uncond_consent_inventories,
                })

    @http.route(['/mail/consent/confirm'], type='json', auth='public', website=True)
    def consent_confirm(self, inventory_id=0, consent_id=0, partner_id=0, mailing_title='', confirm=False, **kw):
        inventory = request.env['gdpr.inventory'].sudo().browse(int(inventory_id))
        partner = request.env['res.partner'].sudo().browse(int(partner_id))
        if inventory and partner:
            if confirm:
                request.env['gdpr.consent'].sudo().add(inventory, partner, partner=partner, name='%s - %s' %(inventory.name, partner.name), msg=mailing_title)
                return 'ok'
            elif consent_id != 0:
                request.env['gdpr.consent'].sudo().browse(consent_id).remove(mailing_title)
            else:
                return 'error'
            return 'ok'
        else:
            return 'error'

    @http.route(['/mail/consent/<int:consent_id>/confirm/<int:confirm>'], type='http', auth='public', website=True)
    def object_consent(self, consent_id, confirm, **post):
    # Wizard to get consent on specified object and purpose (inventory). Mail should have two links: given/withdrawn. If consent is missing, wizard creates it.
        consent = request.env['gdpr.consent'].browse(int(consent_id))
        if confirm == 1:
            request.env['gdpr.consent'].sudo().add(consent.gdpr_id, consent.record_id, partner=consent.partner_id)
        else:
            consent.remove(_('Per mail'))
        return request.website.render('gdpr_mass_mailing.consent_thanks', {'inventory': consent.gdpr_id, 'confirm': confirm})
