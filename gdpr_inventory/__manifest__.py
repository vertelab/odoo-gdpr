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

{
    'name': 'GDPR Inventory',
    'version': '12.0.0.2',
    'category': 'Other',
    'summary': 'Inventory for GDPR',
    'description': """
Basic tool to make your data handling GDPR compliant.

Create inventories of all the private data you handle.

Manage consents of data storage and handling.

Set up rules to govern purpose and life span of inventoried data. Once data is no longer allowed to be stored, it can be automatically overwritten, deleted, hidden or flagged for manual processing.
""",
    'images': ['static/description/event_participant.jpg'],
    'author': 'Vertel AB',
    'website': 'http://www.vertel.se',
    'depends': [
        #'attachment_notebook', 
        'mail', 
        'knowledge', 
        'document'
    ],
    'data': [
        'security/gdpr_security.xml',
        #'security/ir.model.access.csv',
        'gdpr_data.xml',
        'gdpr_view.xml',
        # ~ 'wizard/consent_view.xml',
        #'report/gdpr_report.xml',
    ],
    'demo': ['gdpr_demo.xml'],
    'application': True,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4s:softtabstop=4:shiftwidth=4:
