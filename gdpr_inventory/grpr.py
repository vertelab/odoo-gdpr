# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
from datetime import timedelta

import logging
_logger = logging.getLogger(__name__)

# https://www.privacy-regulation.eu
class gdpr_inventory(models.Model):
    _name = 'gdpr.inventory'
    _inherit = ['mail.thread']

    name = fields.Char()
    state = fields.Selection(selection=[('draft','Draft'),('active','Active'),('closed','Closed')],track_visibility='onchange')
    type_of_personal_data = fields.Selection(selection=[('general','General'),('special','Special Category'),('child','Childs concent'),('criminal','Criminal related')],string="Type",
         help="General: non sensitive personal data,  Special: sensitive personal data, Child concent: personal data concerning under aged persons, Criminal relared:  personal data relating to criminal convictions and offences")
    purpose_limitation = fields.Text(track_visibility='onchange')
    user_id = fields.Many2one(comodel_name="res.users",string="Responsible",track_visibility='onchange')
    lawsection_id = fields.Many2one(comodel_name="gdpr.lawsection",string="Law Section")
    lawsection_desc = fields.Text(string="Law section Explanation")
    concent_desc = fields.Text(string="Concent Explanation")
    concent_add = fields.Text(string="Concent Add",help="Code for concent add")
    concent_remove = fields.Text(string="Concent Remove",help="Code for concent remove")
    website_desc = fields.Html(string="Website Description", translation=True,track_visibility='onchange')
    website_published = fields.Boolean()
    restrict_time_days = fields.Integer(string='Restrict time',help="Number of days before this data will be restricted",track_visibility='onchange')
    restrict_method_id = fields.Many2one(comodel_name="gdpr.restrict_method",string="Restrict Method",track_visibility='onchange')
    restrict_model = fields.Many2one(comodel_name="res.models",string="Restric Model", help="Model (Class) for this Restrition")
    restrict_domain = fields.Text(string="Restrict Domain",help="Domain for identification of personal data of this type")
    fields_ids = fields.Many2many(comodel_name="ir.model.fields",string="Fields",help="Fields with (potential) personal data")
    security_of_processing_ids = fields.Many2many(comodel_name="gdpr.security",string="Security",help="Security of processing",track_visibility='onchange')

    @api.one
    def _partner_ids(self):
        self.partner_ids = self.env['res.partner'].search(self.restrict_domain)
    partner_ids = fields.Many2many(comodel_name="res.partner",compute="_partner_ids")

    @api.one
    def log(self,subject,body):
        id = self.env['mail.message'].create({
                'body': body,
                'subject': subject,
                'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                'res_id': self.id,
                'model': self._name,
                'type': 'notification',})

            
    @api.model
    def cron(self):
        for gdpr in self.env['gdpr.inventory'].search([('state','=','active')]):
            gdpr.resrict_method_id.cron()
            gdpr.log(_('Cron method %s' % gdpr.resrict_method_id.name))

    
class gdpr_lawsection(models.Model):
    """
    1. Processing shall be lawful only if and to the extent that at least one of the following applies: 
=> Article: 9
(a) the data subject has given consent to the processing of his or her personal data for one or more specific purposes; 
=> Article: 7
=> Recital: 42, 171
(b) processing is necessary for the performance of a contract to which the data subject is party or in order to take steps at the request of the data subject prior to entering into a contract;
(c) processing is necessary for compliance with a legal obligation to which the controller is subject;
(d) processing is necessary in order to protect the vital interests of the data subject or of another natural person;
(e) processing is necessary for the performance of a task carried out in the public interest or in the exercise of official authority vested in the controller;
(f) processing is necessary for the purposes of the legitimate interests pursued by the controller or by a third party, except where such interests are overridden by the interests or fundamental rights and freedoms of the data subject which require protection of personal data, in particular where the data subject is a child. 
=> Article: 13, 21
=> Recital: 113, 47
    """
    _name = 'gdpr.lawsection'
    _description = "Lawfullness of processing"
    
    name = fields.Char()
    description = fields.Text()
    concent = fields.Boolean()
    

class gdpr_concent(models.Model):
    """
    1. Where processing is based on consent, the controller shall be able to demonstrate that the data subject has consented to processing of his or her personal data.
    2. If the data subject's consent is given in the context of a written declaration which also concerns other matters, the request for consent shall be presented in a manner which is clearly distinguishable from the other matters, in an intelligible and easily accessible form, using clear and plain language. Any part of such a declaration which constitutes an infringement of this Regulation shall not be binding.
    3. The data subject shall have the right to withdraw his or her consent at any time. The withdrawal of consent shall not affect the lawfulness of processing based on consent before its withdrawal. Prior to giving consent, the data subject shall be informed thereof. It shall be as easy to withdraw as to give consent.
    4. When assessing whether consent is freely given, utmost account shall be taken of whether, inter alia, the performance of a contract, including the provision of a service, is conditional on consent to the processing of personal data that is not necessary for the performance of that contract.
    """
    _name = 'gdpr.concent'
    _description = "Given Concents"
    _inherit = ['mail.thread']
    
    partner_id = fields.Many2one(comodel_name="res.partner")
    @api.model
    def _record_id(self)
        return [(m.name,m.model) for m in self.env['res.model'].search([])]
    record_id = fields.Reference(selection=_record_id(),string="Object",help="Object that is concented for processing of personal data")
    gdpr_id = fields.Many2one(comodel_name='gdpr.inventory',help="Description of concent")
    date = fields.Date(string="Date",help="Date when concent first given") 
    state = fields.selection(selection=[('given','Given'),('withdraw','Withdraw')],string="State",track_visibility='onchange') # transaction log
    
    @api.one
    def concent_add(self,gdpr):
        pass

    @api.one
    def concent_remove(self,gdpr):
        pass
        
    
class gdpr_security(models.Model):
    """
    
        1. Taking into account the state of the art, the costs of implementation and the nature, scope, context and purposes of processing as well as the risk of varying likelihood and severity for the rights and freedoms of natural persons, the controller and the processor shall implement appropriate technical and organisational measures to ensure a level of security appropriate to the risk, including inter alia as appropriate:
        (a) the pseudonymisation and encryption of personal data; 
        => Article: 4
        (b) the ability to ensure the ongoing confidentiality, integrity, availability and resilience of processing systems and services;
        (c) the ability to restore the availability and access to personal data in a timely manner in the event of a physical or technical incident;
        (d) a process for regularly testing, assessing and evaluating the effectiveness of technical and organisational measures for ensuring the security of the processing.
        2. In assessing the appropriate level of security account shall be taken in particular of the risks that are presented by processing, in particular from accidental or unlawful destruction, loss, alteration, unauthorised disclosure of, or access to personal data transmitted, stored or otherwise processed. 
        => Recital: 75
        3. Adherence to an approved code of conduct as referred to in Article 40 or an approved certification mechanism as referred to in Article 42 may be used as an element by which to demonstrate compliance with the requirements set out in paragraph 1 of this Article.
        4. The controller and processor shall take steps to ensure that any natural person acting under the authority of the controller or the processor who has access to personal data does not process them except on instructions from the controller, unless he or she is required to do so by Union or Member State law.
          

        1. Med beaktande av den senaste utvecklingen, genomförandekostnaderna och behandlingens art, omfattning, sammanhang och ändamål samt riskerna, av varierande sannolikhetsgrad och allvar, för fysiska personers rättigheter och friheter ska den personuppgiftsansvarige och personuppgiftsbiträdet vidta lämpliga tekniska och organisatoriska åtgärder för att säkerställa en säkerhetsnivå som är lämplig i förhållande till risken, inbegripet, när det är lämpligt
        a) pseudonymisering och kryptering av personuppgifter, 
        => Artikel: 4
        b) förmågan att fortlöpande säkerställa konfidentialitet, integritet, tillgänglighet och motståndskraft hos behandlingssystemen och -tjänsterna,
        c) förmågan att återställa tillgängligheten och tillgången till personuppgifter i rimlig tid vid en fysisk eller teknisk incident,
        d) ett förfarande för att regelbundet testa, undersöka och utvärdera effektiviteten hos de tekniska och organisatoriska åtgärder som ska säkerställa behandlingens säkerhet.
        2. Vid bedömningen av lämplig säkerhetsnivå ska särskild hänsyn tas till de risker som behandling medför, i synnerhet från oavsiktlig eller olaglig förstöring, förlust eller ändring eller till obehörigt röjande av eller obehörig åtkomst till de personuppgifter som överförts, lagrats eller på annat sätt behandlats. 
        => Grundläggande: 75
        3. Anslutning till en godkänd uppförandekod som avses i artikel 40 eller en godkänd certifieringsmekanism som avses i artikel 42 får användas för att visa att kraven i punkt 1 i den här artikeln följs.
        4. Den personuppgiftsansvarige och personuppgiftsbiträdet ska vidta åtgärder för att säkerställa att varje fysisk person som utför arbete under den personuppgiftsansvariges eller personuppgiftsbiträdets överinseende, och som får tillgång till personuppgifter, endast behandlar dessa på instruktion från den personuppgiftsansvarige, om inte unionsrätten eller medlemsstaternas nationella rätt ålägger honom eller henne att göra det.
    
    """
    _name = 'gdpr.security'
    _description = "Security of processing"
    
    name = fields.Char()
    description = fields.Text()
    
class gdpr_restrict_method(models.Model):
    _name = 'gdpr.restrict_method'
    _description = "Restric Method"
    _inherit = ['mail.thread']
    
    name = fields.Char()
    description = fields.Text()
    type = fields.Selection(selection=[('erase','Erase'),('hide','Hide'),('encrypt','Encrypt'),('pseudo','Pseudonymisation'),('manual','Manual'),('concent','Concent')])
    code = fields.Text()

    @api.one
    def restrict_erase(self,gdpr):
        models = self.env[gdpr.model].search(gdpr.domain)
        self.env[gdpr.model].search(gdpr.domain).unlink()
        gdpr.log(_('Restrict Erase'),','.join(models.mapped('name')))
        
    @api.one
    def restrict_hide(self,gdpr):
        fields.Datetime.to_string(intervals[0][0])
        restrict_date = fields.Date.to_string(fields.Date.today()) - datetime.timedelta(days=gdpr.restrict_time_days)
        models = self.env[gdpr.model].search(gdpr.domain.format({'restrict_date': fields.Date.tostring(fields.Date.today() - datetime.timedelta(days=gdpr.restrict_time_days))})
        self.env[gdpr.model].search(gdpr.domain).write({'active': False})
        gdpr.log(_('Restrict Hide'),models)
        
    @api.one
    def restrict_encrypt(self,gdpr):
        models = self.env[gdpr.model].search(gdpr.domain)
        self.env[gdpr.model].search(gdpr.domain).write({'active': False})
        gdpr.log(_('Restrict Hide'),models)

    @api.one
    def restrict_log(self,gdpr):
        models = self.env[gdpr.model].search(gdpr.domain)
        self.env[gdpr.model].search(gdpr.domain).write({'active': False})
        gdpr.log(_('Restrict Hide'),models)

    @api.one
    def cron(self,gdpr):
        models = self.env[gdpr.model].search(gdpr.domain)
        self.env[gdpr.model].search(gdpr.domain).write({'active': False})
        gdpr.log(_('Restrict Hide'),models)
        
        
class res_partner(models.Model):
    _inherit = 'res.partner'
    
    """ 
    1) search for non inventoried res.partner
    2) button: concents
    3) button: list related gdpr.inventorie (other law sections) 
    4) for each gdpr.inventory list document related to res.partner and gdpr.inventory
    5) list res.partber for each gdpr.inventory
    
    """
    
    @api.one  # depends
    def _gdpr_ids(self):
        self.gdpr_ids = self.env['gdpr.inventory'].search([('state','=','active'),('restrict_method_id.type','!=','concent')]).filtered(lambda g: self.id in g.partner_ids)
    gdpr_ids = fields.Many2many(comodel_name='gdpr.inventory',compute="_gdpr_ids",stored=True)
    
    """
    write: if gdpr.gdpr_method_id.type in (encrypt)
    read: decrypt fields
    """
    