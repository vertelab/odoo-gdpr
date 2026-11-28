# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) {year} {company} info@vertel.se
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
#
# https://www.odoo.com/documentation/14.0/reference/module.html
#
{
    'name': 'GDPR: Inventory Tier Validation',
    'version': '18.0.1.0.0',
    'summary': 'Adds tier validation to the GDPR processing inventory.',
    'category': 'Administration',
    'description': """
Adds tier validation to the GDPR processing inventory.

An inventory must be approved through its configured validation tiers before
it can be activated. Activation is what makes the retention cron act on it, so
the approval gate sits directly in front of the step that starts deleting data.
""",
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-',
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'depends': ["gdpr_inventory","base_tier_validation"],
    'data': ["views/gdpr_inventory_views.xml", "data/tier_definition_data.xml"],
    'demo': [],
    'application': False,
    'installable': True,    
    'auto_install': False,
}
