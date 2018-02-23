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
from openerp import models,  fields,  api,  _
from datetime import timedelta
from random import choice
from openerp.tools.safe_eval import safe_eval
from openerp.exceptions import Warning

import time
import datetime
import dateutil
import pytz

import logging
_logger = logging.getLogger(__name__)

#TODO: logg on restrict method (when its done by cron)


class gdpr_inventory_state(models.Model):
    _name = 'gdpr.inventory.state'

    name = fields.Char(string='Name', required=True)
    technical_name = fields.Char(string='Technical Name', required=True)
    sequence = fields.Integer(string='Sequence')
    fold = fields.Boolean(string='Folded in Kanban View', help='This stage is folded in the kanban view when there are no records in that state to display.')

common_eval_vars = """
Available variables:
* env: Odoo environment.
* time: time python module.
* datetime: datetime python module.
* dateutil: dateutil python module.
* timezone: pytz.timezone python module."""

class gdpr_system(models.Model):
    _name = 'gdpr.system'
    _description = 'GDPR Data System'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')

class gdpr_subject(models.Model):
    _name = 'gdpr.subject'
    _description = 'GDPR Data Subject'

    name = fields.Char(string='Name')

class gdpr_data_type(models.Model):
    _name = 'gdpr.data_type'
    _description = 'GDPR Data Type'

    name = fields.Char(string='Name')

class gdpr_role(models.Model):
    _name = 'gdpr.role'
    _description = 'GDPR Role'

    name = fields.Char(string='Name')

# https://www.privacy-regulation.eu
class gdpr_inventory(models.Model):
    _name = 'gdpr.inventory'
    _description = 'GDPR Inventory'
    _inherit = ['mail.thread']

    @api.model
    def _default_system_id(self):
        return self.env['ir.model.data'].xmlid_to_object('gdpr_inventory.gdpr_system_odoo', False)

    @api.model
    def _default_state_id(self):
        return self.env['gdpr.inventory.state'].search([], order='sequence', limit=1)

    @api.model
    def _default_subject_ids(self):
        return self.env['ir.model.data'].xmlid_to_object('gdpr_inventory.gdpr_data_subject_customer', False)

    @api.model
    def _get_state_selection(self):
        states = self.env['gdpr.inventory.state'].search([], order='sequence')
        return [(state.technical_name, state.name) for state in states]
    
    @api.one
    def _compute_state(self):
        self.state = self.state_id.technical_name

    color = fields.Integer(string='Color Index')
    name = fields.Char(string="Name", translate=True, required=True)
    state_id = fields.Many2one(comodel_name='gdpr.inventory.state', string='State', required=True, default=_default_state_id, track_visibility='onchange')
    state = fields.Selection(selection=_get_state_selection, compute='_compute_state')
    type_of_personal_data = fields.Selection(selection=[('general', 'General'), ('special', 'Special Category'), ('child', 'Childs consent'), ('criminal', 'Criminal related')], string="Type",
         help="General: non sensitive personal data,   Special: sensitive personal data,  Child consent: personal data concerning under aged persons,  Criminal relared:  personal data relating to criminal convictions and offences")
    purpose_limitation = fields.Text(track_visibility='onchange', translate=True, required=True)
    user_id = fields.Many2one(comodel_name="res.users", string="Responsible", track_visibility='onchange', required=True)
    lawsection_id = fields.Many2one(comodel_name="gdpr.lawsection", string="Law Section", required=True, track_visibility='onchange')
    lawsection_description = fields.Html(related='lawsection_id.description', readonly=True, track_visibility='onchange')
    consent = fields.Boolean(related='lawsection_id.consent', track_visibility='onchange')
    lawsection_desc = fields.Html(string="Law section Explanation", track_visibility='onchange')
    data_subject_ids = fields.Many2many(comodel_name='gdpr.subject', string='Data Subjects', default=_default_subject_ids, track_visibility='onchange')
    role = fields.Selection(selection=[('controller', 'Controller'), ('processor', 'Processor')], string='Our Role', default='controller', required=True, track_visibility='onchange')
    data_type_ids = fields.Many2many(comodel_name='gdpr.data_type', string='Data Types', help="A description of the types of data that are stored in this inventory.", track_visibility='onchange')
    data_collection_ids = fields.Many2many(comodel_name='gdpr.system', string='Data Collection', relation='gdpr_inventory_gdpr_system_collection_rel', column1='gdpr_id', column2='system_id', help="The system that is used to collect data for this inventory.", default=_default_system_id, track_visibility='onchange')
    data_storage_ids = fields.Many2many(comodel_name='gdpr.system', string='Data Storage', relation='gdpr_inventory_gdpr_system_storage_rel', column1='gdpr_id', column2='system_id', help="The system that is used to store data for this inventory.", default=_default_system_id, track_visibility='onchange')
    data_sharing_ids = fields.Many2many(comodel_name='res.partner', relation='gdpr_inventory_res_partner_sharing_rel', column1='gdpr_id', column2='partner_id', string='Data Sharing', help="Any partners that we share this data with.", track_visibility='onchange')
    consent_desc = fields.Text(string="consent Explanation")
    consent_add = fields.Text(string="consent Add", help="Code for consent add")
    consent_remove = fields.Text(string="consent Remove", help="Code for consent remove")
    consent_ids = fields.One2many(comodel_name='gdpr.consent', inverse_name='gdpr_id', string='Consents')
    @api.depends('consent_ids')
    @api.one
    def _consent_count(self):
        self.consent_count = len(self.consent_ids)
    consent_count = fields.Integer(string='Consent Count', compute='_consent_count', store=True)
    restrict_time_days = fields.Integer(string='Restrict time', help="Number of days before this data will be restricted", track_visibility='onchange')
    restrict_method_id = fields.Many2one(comodel_name="gdpr.restrict_method", string="Restrict Method", track_visibility='onchange')
    restrict_domain = fields.Text(string='Restrict Domain', help="Domain for identifying records that should be restricted.\n%s\n* restrict_days: Restrict time of this inventory" % common_eval_vars, default='[]')
    restrict_domain_advanced = fields.Boolean(string='Advanced Domain')
    restrict_domain_code = fields.Text(string='Restrict Domain Code', help="Python code that will be executed before domain evaluation. Any variables defined here will be available during domain evaluation.\n%s" % common_eval_vars)
    restrict_code = fields.Text(string='Restriction Code', help="""Python code to run when restricting records.
%s
* inventory: This inventory record.
* objects: The gdpr objects to be restricted (gdpr.object). Actual records to be processed can be accessed through objects.mapped('object_id').""" % common_eval_vars, default = '{}')
    pseudo_values = fields.Text(string='Pseudonymisation Values', help="Custom values used to anonymize fields. Any fields not specified in this dict will be set to False.", default = '{}')
    restrict_type = fields.Selection(string='Restriction Type', related='restrict_method_id.type')
    manual_count = fields.Integer(string='Manual Count', compute='_manual_count', default=0)
    @api.one
    def _manual_count(self):
        self.manual_count = self.env['gdpr.object'].search_count([('manual', '=', True), ('restricted', '=', False), ('gdpr_id', '=', self.id)])
    inventory_model = fields.Many2one(comodel_name="ir.model", string="Inventory Model",  help="Model (Class) for this Inventory")
    inventory_domain = fields.Text(string="Inventory Domain", help="Domain for identification of personal data of this type\n%s" % common_eval_vars, default='[]')
    inventory_domain_advanced = fields.Boolean(string='Advanced Domain')
    inventory_domain_code = fields.Text(string='Restrict Domain Code', help="Python code that will be executed before domain evaluation. Any variables defined here will be available during domain evaluation.\n%s\n* restrict_days: Restrict time of this inventory" % common_eval_vars)
    fields_ids = fields.Many2many(comodel_name="ir.model.fields", string="Fields", relation='gdpr_inventory_ir_model_rel_fields_ids', help="Fields with (potential) personal data")
    partner_fields_ids = fields.Many2many(comodel_name="ir.model.fields", string="Partner Fields", relation='gdpr_inventory_ir_model_rel_partner_fields_ids', help="Fields with personal link")
    partner_domain = fields.Text(string="Partner Domain", help="Domain for identification of partners connected to this personal data")
    @api.depends('object_ids.partner_id')
    @api.one
    def _partner_ids(self):
        self.partner_ids = self.object_ids.mapped('partner_id')
        self.partner_count = len(self.partner_ids)
    partner_ids = fields.Many2many(string='Partners', comodel_name='res.partner', compute='_partner_ids', store=True)
    #~ partner_ids = fields.Many2many(string='Partners', comodel_name='res.partner', relation='gdpr_inventory_rel_res_partner', column1='gdpr_id', column2='partner_id')
    partner_count = fields.Integer(string='Partner Count', compute='_partner_ids', store=True)
    object_ids = fields.One2many(string='Objects', comodel_name='gdpr.object', inverse_name='gdpr_id')
    @api.depends('object_ids')
    @api.one
    def _object_count(self):
        self.object_count = len(self.object_ids)
    object_count = fields.Integer(string='Object Count', compute='_object_count', store=True)
    security_of_processing_ids = fields.Many2many(comodel_name="gdpr.security", string="Security", help="Security of processing", track_visibility='onchange')

    @api.onchange('restrict_method_id')
    def onchange_restrict_method_id(self):
        if self.restrict_method_id:
            self.restrict_code = self.restrict_method_id.code

    @api.onchange('restrict_method_id', 'inventory_model')
    def onchange_verify_hide(self):
        if self.restrict_method_id and self.restrict_method_id.type == 'hide' and self.inventory_model:
            if not self.env['ir.model.fields'].search_count([('model_id', '=', self.inventory_model.id), ('name', '=', 'active')]):
                raise Warning("Model %s (%s) can not be hidden because it does not have an 'active' field." % (self.inventory_model.name, self.inventory_model.model))

    #~ @api.one
    #~ def _partner_ids(self):
        #~ self.partner_ids = self.env['res.partner'].search(self.inventory_domain)
    #~ partner_ids = fields.Many2many(comodel_name="res.partner", compute="_partner_ids")

    @api.one
    def create_random_objects(self, count=1):
        records = self.env[self.inventory_model.model].search([])
        partners = self.env['res.partner'].search([])
        while count > 0:
            self.env['gdpr.object'].create({
                'object_id': '%s,%s' % (records._name, choice(records).id),
                'partner_id': choice(partners).id,
                'gdpr_id': self.id,
            })
            count -= 1

    @api.one
    def log(self, subject, body):
        id = self.env['mail.message'].create({
            'body': body,
            'subject': subject,
            'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
            'res_id': self.id,
            'model': self._name,
            'type': 'notification',
        })

    @api.multi
    def action_view_objects(self):
        object_ids = [r['object_res_id'] for r in self.env['gdpr.object'].search_read([('gdpr_id', '=', self.id)], ['object_res_id'])]
        return {
            'type': u'ir.actions.act_window',
            'target': u'current',
            'res_model': self.inventory_model.model,
            'view_mode': u'tree,form',
            'domain': [('id', 'in', object_ids)],
            'context': {},
        }

    @api.multi
    def action_view_manual_objects(self):
        return {
            'type': u'ir.actions.act_window',
            'target': u'current',
            'res_model': 'gdpr.object',
            'view_mode': u'tree,form',
            'domain': [('gdpr_id', '=', self.id)],
            'context': {'search_default_manual': 1, 'search_default_unrestricted': 1},
        }
        
    @api.model
    def cron_restrictions(self):
        for gdpr in self.env['gdpr.inventory'].search([('state', '=', 'active')]):
            gdpr.resrict_method_id.cron()
            gdpr.log(_('Cron method %s' % gdpr.resrict_method_id.name))

    @api.one
    def update_partner_ids(self):
        """Update partner_ids field."""
        pass

    @api.model
    def cron_partner_ids(self):
        """Update all connections between inventories and partners."""
        pass

    @api.one
    def update_object_ids(self):
        # Remove non-existing objects
        model = self.env[self.inventory_model.model]
        if model.fields_get('active'):
            object_ids = [d['id'] for d in model.search_read([('active', 'in', (True, False))], ['id'])]
        else:
            object_ids = [d['id'] for d in model.search_read([], ['id'])]
        self.env['gdpr.object'].search([('gdpr_id', '=', self.id), ('object_res_id', 'not in', object_ids)]).unlink()

        # Update all matching objects
        global_vars = self.env['gdpr.restrict_method'].get_eval_context()
        if self.inventory_domain_advanced:
            eval(compile(self.inventory_domain_code, __name__, 'exec'), global_vars)
        _logger.warn(global_vars)
        objects = model.search(safe_eval(self.inventory_domain, global_vars))
        if self.object_ids:
            objects |= self.object_ids.mapped('object_id')
        _logger.warn(objects)
        for o in objects:
            partners = self.env['res.partner'].browse([])
            for p in self.partner_fields_ids:
                if p.ttype == 'integer' and getattr(o, p.name):
                    # Assume that this is the ID of a partner
                    partners |= self.env['res.partner'].browse(getattr(o, p.name))
                else:
                    partners |= getattr(o, p.name)
                _logger.warn(partners)
            for partner in partners:
                if not self.env['gdpr.object'].search([('gdpr_id', '=', self.id), ('object_id', '=', '%s,%s' %(self.inventory_model.model, o.id)), ('partner_id', '=', partner.id)]):
                    self.env['gdpr.object'].create({
                        'gdpr_id': self.id,
                        'object_id': '%s,%s' %(o._name, o.id),
                        'partner_id': partner.id,
                    })

    @api.one
    def restrict_objects(self):
        """
        Check if any records meet the restrict critera and perform restriction according to the chosen restrict method.
        """
        if self.restrict_method_id:
            model = self.inventory_model.model
            global_vars = self.env['gdpr.restrict_method'].get_eval_context(restrict_days=self.restrict_time_days)
            if self.restrict_domain_advanced:
                eval(compile(self.restrict_domain_code, __name__, 'exec'), global_vars)
            domain = safe_eval(self.restrict_domain, global_vars)
            object_ids = [o['id'] for o in self.env[model].search_read(domain, ['id'])]
            _logger.debug('restrict_objects object_ids: %s' % object_ids)
            domain = [('restricted', '!=', True), ('gdpr_id', '=', self.id), ('object_res_id', 'in', object_ids)]
            if self.lawsection_id.consent:
                gdpr_o_ids = [o['gdpr_object_id'][0] for o in self.env['gdpr.consent'].search_read([('state', '=', 'withdrawn'), ('record_id', 'in', [('%s,%s' % (model, id)) for id in object_ids]), ('gdpr_id', '=', self.id)], ['gdpr_object_id'])]
                domain.append(('id', 'in', gdpr_o_ids))
            _logger.debug('restrict_objects domain: %s' % domain)
            objects = self.env['gdpr.object'].search(domain)
            if objects:
                self.restrict_method_id.restrict_objects(self, objects)

    @api.multi
    def cron_object_ids(self):
        self.search([]).update_object_ids()

    @api.multi
    def act_gdpr_inventory_2_gdpr_res_partner(self):
        return {
            'name': 'Res Partner 2 GDPR Inventory Partner',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'view_type': 'kanban',
            'domain': [('id', 'in', self.partner_ids.mapped('id'))],
            'context': {},
        }

    @api.model
    def _read_state_id(self, present_ids, domain, **kwargs):
        states = self.env['gdpr.inventory.state'].search([], order='sequence').name_get()
        return states, None

    _group_by_full = {
        'state_id': _read_state_id,
    }

class gdpr_lawsection(models.Model):
    """
    1. Processing shall be lawful only if and to the extent that at least one of the following applies:
=> Article: 9
(a) the data subject has given consent to the processing of his or her personal data for one or more specific purposes;
=> Article: 7
=> Recital: 42,  171
(b) processing is necessary for the performance of a contract to which the data subject is party or in order to take steps at the request of the data subject prior to entering into a contract;
(c) processing is necessary for compliance with a legal obligation to which the controller is subject;
(d) processing is necessary in order to protect the vital interests of the data subject or of another natural person;
(e) processing is necessary for the performance of a task carried out in the public interest or in the exercise of official authority vested in the controller;
(f) processing is necessary for the purposes of the legitimate interests pursued by the controller or by a third party,  except where such interests are overridden by the interests or fundamental rights and freedoms of the data subject which require protection of personal data,  in particular where the data subject is a child.
=> Article: 13,  21
=> Recital: 113,  47
    """
    _name = 'gdpr.lawsection'
    _description = "Lawfullness of processing"

    name = fields.Char(string='Name')
    description = fields.Html(string='Description')
    consent = fields.Boolean(string='Consent')


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
    state = fields.Selection(selection=[('given', 'Given'), ('withdrawn', 'Withdrawn')], string="State", track_visibility='onchange') # transaction log
    
    #~ object_id = fields.Reference(string='Object', selection='_reference_models', compute='_get_object_id', inverse='_set_object_id', search='_search_object_id')
    #~ object_model = fields.Char(string='Object Model')
    #~ object_res_id = fields.Integer(string='Object ID')
    

    #~ @api.one
    #~ def _get_object_id(self):
        #~ if self.object_model and self.object_res_id:
            #~ self.object_id = self.env[self.object_model].search([('id', '=', self.object_res_id)])
    @api.one
    def remove(self, msg):
        self.state = 'withdrawn'
        self.env['mail.message'].create({
            'body': msg.replace('\n', '<BR/>'),
            'subject': 'Consent withdrawn',
            'author_id': self.env.user.partner_id.id,
            'res_id': self.id,
            'model': self._name,
            'type': 'notification',})

class gdpr_security(models.Model):
    """

        1. Taking into account the state of the art,  the costs of implementation and the nature,  scope,  context and purposes of processing as well as the risk of varying likelihood and severity for the rights and freedoms of natural persons,  the controller and the processor shall implement appropriate technical and organisational measures to ensure a level of security appropriate to the risk,  including inter alia as appropriate:
        (a) the pseudonymisation and encryption of personal data;
        => Article: 4
        (b) the ability to ensure the ongoing confidentiality,  integrity,  availability and resilience of processing systems and services;
        (c) the ability to restore the availability and access to personal data in a timely manner in the event of a physical or technical incident;
        (d) a process for regularly testing,  assessing and evaluating the effectiveness of technical and organisational measures for ensuring the security of the processing.
        2. In assessing the appropriate level of security account shall be taken in particular of the risks that are presented by processing,  in particular from accidental or unlawful destruction,  loss,  alteration,  unauthorised disclosure of,  or access to personal data transmitted,  stored or otherwise processed.
        => Recital: 75
        3. Adherence to an approved code of conduct as referred to in Article 40 or an approved certification mechanism as referred to in Article 42 may be used as an element by which to demonstrate compliance with the requirements set out in paragraph 1 of this Article.
        4. The controller and processor shall take steps to ensure that any natural person acting under the authority of the controller or the processor who has access to personal data does not process them except on instructions from the controller,  unless he or she is required to do so by Union or Member State law.


        1. Med beaktande av den senaste utvecklingen,  genomförandekostnaderna och behandlingens art,  omfattning,  sammanhang och ändamål samt riskerna,  av varierande sannolikhetsgrad och allvar,  för fysiska personers rättigheter och friheter ska den personuppgiftsansvarige och personuppgiftsbiträdet vidta lämpliga tekniska och organisatoriska åtgärder för att säkerställa en säkerhetsnivå som är lämplig i förhållande till risken,  inbegripet,  när det är lämpligt
        a) pseudonymisering och kryptering av personuppgifter,
        => Artikel: 4
        b) förmågan att fortlöpande säkerställa konfidentialitet,  integritet,  tillgänglighet och motståndskraft hos behandlingssystemen och -tjänsterna,
        c) förmågan att återställa tillgängligheten och tillgången till personuppgifter i rimlig tid vid en fysisk eller teknisk incident,
        d) ett förfarande för att regelbundet testa,  undersöka och utvärdera effektiviteten hos de tekniska och organisatoriska åtgärder som ska säkerställa behandlingens säkerhet.
        2. Vid bedömningen av lämplig säkerhetsnivå ska särskild hänsyn tas till de risker som behandling medför,  i synnerhet från oavsiktlig eller olaglig förstöring,  förlust eller ändring eller till obehörigt röjande av eller obehörig åtkomst till de personuppgifter som överförts,  lagrats eller på annat sätt behandlats.
        => Grundläggande: 75
        3. Anslutning till en godkänd uppförandekod som avses i artikel 40 eller en godkänd certifieringsmekanism som avses i artikel 42 får användas för att visa att kraven i punkt 1 i den här artikeln följs.
        4. Den personuppgiftsansvarige och personuppgiftsbiträdet ska vidta åtgärder för att säkerställa att varje fysisk person som utför arbete under den personuppgiftsansvariges eller personuppgiftsbiträdets överinseende,  och som får tillgång till personuppgifter,  endast behandlar dessa på instruktion från den personuppgiftsansvarige,  om inte unionsrätten eller medlemsstaternas nationella rätt ålägger honom eller henne att göra det.

    """
    _name = 'gdpr.security'
    _description = "Security of processing"

    name = fields.Char()
    description = fields.Text()

class gdpr_restrict_method(models.Model):
    _name = 'gdpr.restrict_method'
    _description = "Restrict Method"
    _inherit = ['mail.thread']

    name = fields.Char()
    description = fields.Text()
    type = fields.Selection(selection=[('erase', 'Erase'), ('hide', 'Hide'), ('encrypt', 'Encrypt'), ('pseudo', 'Pseudonymisation'), ('manual', 'Manual'), ('code', 'Code')])
    code = fields.Text()

    @api.one
    def restrict_erase(self, gdpr):
        models = self.env[gdpr.model].search(gdpr.domain)
        self.env[gdpr.model].search(gdpr.domain).unlink()
        gdpr.log(_('Restrict Erase'), ', '.join(models.mapped('name')))

    @api.one
    def restrict_hide(self, gdpr):
        fields.Datetime.to_string(intervals[0][0])
        restrict_date = fields.Date.to_string(fields.Date.today()) - datetime.timedelta(days=gdpr.restrict_time_days)
        models = self.env[gdpr.model].search(gdpr.domain.format({
            'restrict_date': fields.Date.tostring(fields.Date.today() - datetime.timedelta(days=gdpr.restrict_time_days))
        }))
        self.env[gdpr.model].search(gdpr.domain).write({'active': False})
        gdpr.log(_('Restrict Hide'), models)

    @api.one
    def restrict_encrypt(self, gdpr):
        models = self.env[gdpr.model].search(gdpr.domain)
        self.env[gdpr.model].search(gdpr.domain).write({'active': False})
        gdpr.log(_('Restrict Hide'), models)

    @api.one
    def restrict_log(self, gdpr):
        models = self.env[gdpr.model].search(gdpr.domain)
        self.env[gdpr.model].search(gdpr.domain).write({'active': False})
        gdpr.log(_('Restrict Hide'), models)

    @api.one
    def cron(self, gdpr):
        models = self.env[gdpr.model].search(gdpr.domain)
        self.env[gdpr.model].search(gdpr.domain).write({'active': False})
        gdpr.log(_('Restrict Hide'), models)

    @api.one
    def restrict_objects(self, inventory, objects):
        """
        Perform restriction.
        :param inventory: The inventory that the objects belong to.
        :param objects: The GDPR objects (gdpr.object) that should be restricted.
        """
        if self.type == 'erase':
            objects.mapped('object_id').unlink()
            objects.unlink()
        elif self.type == 'hide':
            if hasattr(objects, 'active'):
                objects.mapped('object_id').write({'active': False})
                objects.write({'restricted': True})
        elif self.type == 'encrypt':
            pass
        elif self.type == 'pseudo':
            values = safe_eval(inventory.pseudo_values, self.get_eval_context())
            for field in inventory.fields_ids:
                if field.name not in values:
                    values[field.name] = False
            objects.mapped('object_id').write(values)
            objects.write({'restricted': True})
        elif self.type == 'manual':
            objects.write({'manual': True})
            # TODO: Button to list expired records.
            pass
        elif self.type == 'code':
            safe_eval(inventory.restrict_code, self.get_eval_context(inventory=inventory, objects=objects), mode='exec')

    @api.model
    def get_eval_context(self, **kw):
        context = {
            # python libs
            'time': time,
            'datetime': datetime,
            'dateutil': dateutil,
            # NOTE: only `timezone` function. Do not provide the whole `pytz` module as users
            #       will have access to `pytz.os` and `pytz.sys` to do nasty things...
            'timezone': pytz.timezone,
            # orm
            'env': self.env,
        }
        context.update(kw)
        return context

class gdpr_object(models.Model):
    _name = 'gdpr.object'

    @api.one
    def _get_name(self):
        if self.object_id and hasattr(self.object_id, 'name'):
            self.name = self.object_id.name
        elif self.object_id:
            self.name = '%s, %s' % (self.object_id._name, self.object_id.id)
        else:
            self.name = 'gdpr.object, %s' % self.id

    name = fields.Char(string='Name', compute='_get_name')
    gdpr_id = fields.Many2one(string='Inventory', comodel_name='gdpr.inventory')
    object_id = fields.Reference(string='Object', selection='_reference_models', compute='_get_object_id', inverse='_set_object_id', search='_search_object_id')
    object_model = fields.Char(string='Object Model')
    object_res_id = fields.Integer(string='Object ID')
    partner_id = fields.Many2one(string='Partners', comodel_name='res.partner')
    restricted = fields.Boolean(string='Restricted', help="This record has been restricted.")
    manual = fields.Boolean(string='Manual Action Required', help="This record needs attention.")

    @api.one
    def _get_object_id(self):
        if self.object_model and self.object_res_id:
            self.object_id = self.env[self.object_model].search([('id', '=', self.object_res_id)])

    @api.one
    def _set_object_id(self):
        if self.object_id:
            self.object_res_id = self.object_id.id
            self.object_model = self.object_id._name
        else:
            self.object_res_id = False
            self.object_model = False

    @api.model
    def _search_object_id(self, operator, value):
        _logger.debug('_search_object_id; operator: %s, value: %s' % (operator, value))
        if operator in ('in', 'not in'):
            if operator == 'in':
                op_m = '='
                ao1 = '&'
                ao2 = '|'
            else:
                op_m = '!='
                ao1 = '|'
                ao2 = '&'
            ids = {}
            for v in value:
                m, id = v.split(',')
                if m not in ids:
                    ids[m] = []
                ids[m].append(int(id))
            res = []
            for model in ids:
                if res:
                    res = [ao2] + res
                res += [ao1, ('object_model', op_m, model), ('object_res_id', operator, ids[model])]
        elif value:
            res = ['&', ('object_model', operator, value.split(',')[0]), ('object_res_id', operator, int(value.split(',')[1]))]
        else:
            res = ['&', ('object_model', operator, value), ('object_res_id', operator, value)]
        _logger.debug(res)
        return res

    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].search([('state', '!=', 'manual')])
        return [(model.model, model.name) for model in models]

class res_partner(models.Model):
    _inherit = 'res.partner'

    """
    1) search for non inventoried res.partner
    2) button: consents
    3) button: list related gdpr.inventorie (other law sections)
    4) for each gdpr.inventory list document related to res.partner and gdpr.inventory
    5) list res.partber for each gdpr.inventory

    """
    @api.one
    def _gdpr_ids(self):
        self.gdpr_ids = self.env['gdpr.object'].search([('partner_id', '=', self.id)]).mapped('gdpr_id')
    gdpr_ids = fields.Many2many(string='GDPRs', comodel_name='gdpr.inventory', compute='_gdpr_ids')
    #~ gdpr_ids = fields.Many2many(string='GDPRs', comodel_name='gdpr.inventory', relation='gdpr_inventory_rel_res_partner', column1='partner_id', column2='gdpr_id', compute='_gdpr_ids', store=True)
    @api.one
    def _get_gdpr_count(self):
        self.gdpr_count = len(self.gdpr_ids)
    gdpr_count = fields.Integer(string='# Inventories', compute='_get_gdpr_count')

    consent_ids = fields.One2many(string='Consents', comodel_name='gdpr.consent', inverse_name='partner_id')
    @api.one
    def _get_consent_count(self):
        self.consent_count = len(self.consent_ids)
    consent_count = fields.Integer(string='# Consents', compute='_get_consent_count')

    gdpr_object_ids = fields.One2many(comodel_name='gdpr.object', inverse_name='partner_id', string='GDPR Objects')
    @api.one
    def _get_gdpr_object_count(self):
        self.gdpr_object_count = len(self.gdpr_object_ids)
    gdpr_object_count = fields.Integer(string='# Objects', compute='_get_gdpr_object_count')

    @api.multi
    def action_gdpr_inventory(self):
        action = self.env['ir.actions.act_window'].for_xml_id('gdpr_inventory', 'action_gdpr_inventory')
        action['domain'] = [('partner_ids', '=', self.id)]
        return action

    @api.multi
    def action_gdpr_objects(self):
        action = self.env['ir.actions.act_window'].for_xml_id('gdpr_inventory', 'action_gdpr_object')
        action['domain'] = [('partner_ids', '=', self.id)]
        return action

    @api.multi
    def act_res_partner_2_gdpr_inventory(self):
        return {
            'name': 'Res Partner 2 GDPR Inventory',
            'res_model': 'gdpr.inventory',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'view_type': 'kanban',
            'domain': [('id', 'in', self.gdpr_ids.mapped('id'))],
            'context': {},
        }

    """
    write: if gdpr.gdpr_method_id.type in (encrypt)
    read: decrypt fields
    """

class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    @api.one
    def _consent_ids(self):
        self.consent_ids = self.env['gdpr.consent'].search([('gdpr_object_id.object_id', '=', '%s,%s' % (self._name, self.id),)])
    consent_ids = fields.One2many(comodel_name='gdpr.consent', compute='_consent_ids')

