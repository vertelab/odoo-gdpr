import json
import logging

from odoo import http, _
from odoo.http import request, content_disposition

_logger = logging.getLogger(__name__)


class GdprPortal(http.Controller):
    """Data subject rights in the portal.

    The lookup itself is the platform's `privacy.lookup.wizard`. This
    controller does not search for personal data on its own — it runs the
    platform lookup for the logged-in partner and presents the result.
    """

    def _get_partner(self):
        return request.env.user.partner_id

    def _run_lookup(self):
        """Run the platform lookup for the current user and log it.

        The search and the logging ambos live on `gdpr.privacy.lookup` so that
        they can be tested without an HTTP request context.
        """
        partner = self._get_partner()
        return request.env['gdpr.privacy.lookup'].run_for_partner(partner)

    def _group_lines(self, wizard):
        """Group lookup lines by model: {model_name: count}.

        The list shows model and count, not field values. Field-level content
        belongs to the JSON export, where it is filtered by the inventory.
        """
        grouped = {}
        for line in wizard.line_ids:
            key = line.res_model or _('Unknown')
            grouped[key] = grouped.get(key, 0) + 1
        return sorted(grouped.items())

    @http.route(['/my/gdpr'], type='http', auth='user', website=True)
    def portal_gdpr(self, **kw):
        partner = self._get_partner()
        wizard = self._run_lookup()
        consents = request.env['gdpr.consent'].sudo().search([
            ('partner_id', '=', partner.id),
        ])
        values = {
            'page_name': 'gdpr',
            'partner': partner,
            'holdings': self._group_lines(wizard),
            'holding_count': len(wizard.line_ids),
            'consents': consents,
            'request_count': request.env['gdpr.access.request'].sudo().search_count([
                ('partner_id', '=', partner.id),
            ]),
        }
        return request.render('gdpr_portal.portal_gdpr', values)

    @http.route(['/my/gdpr/export'], type='http', auth='user', website=True)
    def portal_gdpr_export(self, **kw):
        """Article 20 — machine-readable export of the data subject's data.

        Only fields the inventory designates as personal data are included
        (`gdpr.inventory.fields_ids`). A record whose model has no inventory
        contributes only its reference, never its field values — an
        uninventoried model has not been assessed for what is personal.
        """
        partner = self._get_partner()
        wizard = self._run_lookup()

        Inventory = request.env['gdpr.inventory'].sudo()
        payload = {
            'data_subject': {
                'name': partner.name,
                'email': partner.email,
            },
            'generated_at': fields_datetime(),
            'records': [],
        }

        for line in wizard.line_ids:
            model_name = line.res_model
            record_ref = '%s,%s' % (model_name, line.res_id)
            entry = {'model': model_name, 'reference': record_ref}

            inventories = Inventory.search([
                ('inventory_model.model', '=', model_name),
                ('state', '=', 'active'),
            ])
            field_names = set()
            for inventory in inventories:
                field_names.update(inventory.fields_ids.mapped('name'))

            if field_names and model_name in request.env:
                try:
                    record = request.env[model_name].sudo().browse(line.res_id)
                    if record.exists():
                        entry['fields'] = {
                            name: _jsonable(record[name])
                            for name in sorted(field_names)
                            if name in record._fields
                        }
                except Exception as error:  # noqa: BLE001 - export must not fail
                    _logger.warning(
                        'gdpr_portal export: could not read %s: %s',
                        record_ref, error)
                    entry['note'] = _('Field values could not be read.')
            else:
                entry['note'] = _(
                    'No active inventory designates personal data fields for '
                    'this model. Only the reference is disclosed.')

            payload['records'].append(entry)

        body = json.dumps(payload, ensure_ascii=False, indent=2)
        filename = 'personal-data-%s.json' % (partner.id,)
        return request.make_response(
            body,
            headers=[
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )

    @http.route(['/my/gdpr/consent/<int:consent_id>/withdraw'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_consent_withdraw(self, consent_id, **kw):
        """Article 7.3 — withdrawal must be as easy as giving consent."""
        partner = self._get_partner()
        consent = request.env['gdpr.consent'].sudo().search([
            ('id', '=', consent_id),
            ('partner_id', '=', partner.id),
        ], limit=1)
        if consent and consent.state != 'withdrawn':
            consent.remove(_('Withdrawn by the data subject in the portal.'))
        return request.redirect('/my/gdpr')


def fields_datetime():
    from odoo import fields
    return fields.Datetime.now().isoformat(timespec='seconds')


def _jsonable(value):
    """Best-effort conversion of an ORM value to something JSON can carry."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    # recordsets, bytes, html objects: fall back to their text form
    try:
        return str(value)
    except Exception:  # noqa: BLE001
        return None
