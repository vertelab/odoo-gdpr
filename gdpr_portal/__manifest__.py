# -*- coding: utf-8 -*-
{
    'name': 'GDPR: Subject Portal',
    'version': '18.0.1.0.0',
    'summary': 'Data subject access, portability and consent withdrawal in the portal.',
    'category': 'Administration',
    'description': """
GDPR: Subject Portal
====================

Gives a logged-in portal user the rights the GDPR grants them:

- **Article 15 — access.** The portal lists where the user's personal data is
  held, using the platform privacy lookup. The list shows model and record
  count, not field values.
- **Article 20 — portability.** The user can download their personal data as
  JSON. Only fields the inventory designates as personal data are included.
- **Article 7.3 — withdrawal.** A consent can be withdrawn from the portal as
  easily as it was given.

Each lookup is recorded in `privacy.log` with the name and email anonymised.
""",
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-gdpr/gdpr_portal',
    'license': 'AGPL-3',
    'depends': [
        'portal',
        'website',
        'gdpr_inventory',
        'privacy_lookup',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/portal_security.xml',
        'views/gdpr_access_request_views.xml',
        'views/portal_templates.xml',
        'report/gdpr_access_request_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
