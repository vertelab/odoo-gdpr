# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP,  Open Source Management Solution,  third party addon
#    Copyright (C) 2004-2018 Vertel AB (<http://vertel.se>).
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
from openerp.exceptions import Warning
from openerp import tools

class gdpr_report_inventory(models.Model):
    _name = 'gdpr.report.inventory'
    _description = 'GDPR Inventory Statistics'
    _auto = False
    _rec_name = 'color'
    
    
    color = fields.Integer(string='Color Index')
    name = fields.Char(string="Name", translate=True, required=True)
    state_id = fields.Many2one(comodel_name='gdpr.inventory.state', string='State', track_visibility='onchange')
    type_of_personal_data = fields.Selection(selection=[('general', 'General'), ('special', 'Special Category'), ('child', 'Childs consent'), ('criminal', 'Criminal related')], string="Type",
         help="General: non sensitive personal data,   Special: sensitive personal data,  Child consent: personal data concerning under aged persons,  Criminal relared:  personal data relating to criminal convictions and offences")
    purpose_limitation = fields.Text(track_visibility='onchange', translate=True, required=True)
    user_id = fields.Many2one(comodel_name="res.users", string="Responsible", track_visibility='onchange', required=True)
    lawsection_id = fields.Many2one(comodel_name="gdpr.lawsection", string="Law Section", required=True)
    consent = fields.Boolean(related='lawsection_id.consent')
    consent_ids = fields.One2many(comodel_name='gdpr.consent', inverse_name='gdpr_id', string='Consents')
    @api.depends('consent_ids')
    @api.one
    def _consent_count(self):
        self.consent_count = len(self.consent_ids)
    consent_count = fields.Integer(string='Consent Count', compute='_consent_count', store=True)
    restrict_time_days = fields.Integer(string='Restrict time', help="Number of days before this data will be restricted", track_visibility='onchange')
    restrict_method_id = fields.Many2one(comodel_name="gdpr.restrict_method", string="Restrict Method", track_visibility='onchange')
    restrict_type = fields.Selection(string='Restriction Type', related='restrict_method_id.type')
    inventory_model = fields.Many2one(comodel_name="ir.model", string="Inventory Model",  help="Model (Class) for this Inventory")
    @api.depends('object_ids.partner_id')
    @api.one
    def _partner_ids(self):
        self.partner_ids = self.object_ids.mapped('partner_id')
        self.partner_count = len(self.partner_ids)
    partner_ids = fields.Many2many(string='Partners', comodel_name='res.partner', compute='_partner_ids', store=True) 
    partner_count = fields.Integer(string='Partner Count', compute='_partner_ids', store=True)
    object_ids = fields.One2many(string='Objects', comodel_name='gdpr.object', inverse_name='gdpr_id')
    @api.depends('object_ids')
    @api.one
    def _object_count(self):
        self.object_count = len(self.object_ids)
    object_count = fields.Integer(string='Object Count', compute='_object_count', store=True)
    


    def _select(self):
        select_str = """
             SELECT min(id),
                 color,
                    name,
                    state_id,
                    type_of_personal_data,
                    purpose_limitation,
                    user_id,
                    lawsection_id,
                    consent_count,
                    restrict_time_days,
                    restrict_method_id,
                    restrict_type,
                    inventory_model,
                    partner_count
        """
        return select_str

    def _from(self):
        from_str = """
                gdpr_inventory
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY ( 
                  color,
                  state_id,
                  type_of_personal_data,
                  user_id,
                  lawsection_id, 
                  restrict_method_id,
                  restrict_type,
                  inventory_model
        """
        return group_by_str

    def init(self, cr):
        # self._table = sale_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM  %s 
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: