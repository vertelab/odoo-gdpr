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
from openerp import http
from openerp.http import request

import logging
_logger = logging.getLogger(__name__)

# https://www.privacy-regulation.eu
class gdpr_inventory(models.Model):
    _inherit = 'gdpr.inventory'

    website_desc = fields.Html(string="Website Description",  translation=True, track_visibility='onchange', translate=True)
    website_published = fields.Boolean(string='Website Published')
    parent_id = fields.Many2one(comodel_name="gdpr.inventory")
    sequence = fields.Integer(string='Sequence')
    website_inventory_ids = fields.One2many(comodel_name='gdpr.inventory',inverse_name='parent_id',string="Related inventories",help='Related inventories that is included in this webdescription',)
    @api.one
    def _website_lawsection_list(self):
        lawsections = [n.lower() for n in [self.lawsection_id.name] + self.website_inventory_ids.mapped('lawsection_id').mapped('name')]
        if len(lawsections) > 0:
            self.website_lawsection_list = (_('%s and %s') % (','.join(lawsections[:-1]),lawsections[-1])).capitalize()
        else:
            self.website_lawsection_list = lawsections[0].capitalize()
    website_lawsection_list = fields.Char(compute='_website_lawsection_list')


class gdpr_category(models.Model):
    _inherit = 'gdpr.category'

    website_published = fields.Boolean(string='Website Published')
    website_desc = fields.Html(string="Website Description",  translation=True, track_visibility='onchange', translate=True)
    @api.one
    def _website_inventory_ids(self):
        self.website_inventory_ids = self.inventory_ids.filetered(lambda i: i.website_published == True).sorted(lambda i: i.sequence)
    website_inventory_ids = fields.One2many(comodel_name='gdpr.inventory',compute='_website_inventory_ids')


class GDPRController(http.Controller):

    @http.route(['/gdpr/main/<model("res.partner"):partner>'], type='http', auth="public", website=True)
    def gdpr_main(self, partner=None, **post):
        inventories = request.env['gdpr.inventory'].search_read(
            [
                ('partner_ids', 'in', partner.id),
                ('state_id', '=', request.env.ref('gdpr_inventory.inventory_state_active').id),
                ('website_published', '=', True)
            ],
            ['name', 'website_desc', 'state_id'])
        return request.website.render('website_gdpr.gdpr_main_page', {'inventories': inventories, 'partner': partner.name})

    @http.route(['/gdpr/inventories'], type='http', auth="public", website=True)
    def gdpr_inventories(self, partner=None, **post):
        categories = request.env['gdpr.category'].sudo().search([])
        category_list = []
        for category in categories:
            inventories = request.env['gdpr.inventory'].sudo().search([
                ('state_id', '=', request.env.ref('gdpr_inventory.inventory_state_active').id),
                ('website_published', '=', True),
                ('category', '=', category.id)
            ])
            if len(inventories) > 0:
                inventory_list = inventories.mapped('website_inventory_ids')
                if len(inventory_list) > 0:
                    category_list.append({
                        'category': category,
                        'inventories': inventory_list,
                    })
        return request.website.render('website_gdpr.gdpr_inventory_page', {
            'categories': category_list,
        })
