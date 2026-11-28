import json

from odoo import api, fields, models, _


class GdprAccessResponse(models.Model):
    """Article 15 response assembled from a privacy lookup.

    The response lists the categories of data held, the purposes, the
    recipients and the retention periods — not the raw field values. Raw
    values belong in the Article 20 export, which is scoped by the inventory.

    A record that may contain data about more than one person is flagged for
    manual review: the module does not attempt to split third-party data out
    of a shared record, because guessing that split is worse than flagging it.
    """

    _name = 'gdpr.access.response'
    _description = 'GDPR Access Response (Article 15)'
    _inherit = ['mail.thread']
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: _('New'))
    request_id = fields.Many2one(
        'gdpr.access.request', string='Access Request', ondelete='cascade')
    partner_id = fields.Many2one(
        'res.partner', string='Data Subject', required=True, ondelete='cascade')
    lookup_line_count = fields.Integer(
        string='Records Found', readonly=True)
    needs_manual_review = fields.Boolean(
        string='Manual Review Required', readonly=True,
        help='At least one record may hold data about more than one person. '
             'The response cannot separate them automatically.')
    review_reason = fields.Text(string='Review Reason', readonly=True)
    body = fields.Html(string='Response Content', readonly=True)
    document = fields.Binary(string='Document', attachment=True, copy=False)
    filename = fields.Char()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'gdpr.access.response') or _('New')
        return super().create(vals_list)

    @api.model
    def _build_for_partner(self, partner):
        """Assemble the response content for one data subject."""
        wizard = self.env['privacy.lookup.wizard'].sudo().create({
            'name': partner.name or '',
            'email': partner.email or '',
        })
        wizard.action_lookup()

        Inventory = self.env['gdpr.inventory'].sudo()
        sections = []
        review_reasons = []

        for line in wizard.line_ids:
            model_name = line.res_model
            inventories = Inventory.search([
                ('inventory_model.model', '=', model_name),
                ('state', '=', 'active'),
            ])
            if not inventories:
                sections.append({
                    'model': model_name,
                    'reference': '%s,%s' % (model_name, line.res_id),
                    'inventories': [],
                })
                continue

            for inventory in inventories:
                sections.append({
                    'model': model_name,
                    'reference': '%s,%s' % (model_name, line.res_id),
                    'inventory': inventory.name,
                    'purpose': inventory.purpose_limitation or '',
                    'legal_basis': inventory.lawsection_id.display_name or '',
                    'recipients': ', '.join(
                        inventory.recipient_category_ids.mapped('name')
                        + inventory.data_sharing_ids.mapped('name')),
                    'retention': (
                        _('%s months') % inventory.retention_months
                        if inventory.retention_months else ''),
                })

            # Third-party data: a record that links to more than one partner
            # cannot be split reliably.
            if model_name in self.env and 'partner_id' in self.env[model_name]._fields:
                try:
                    record = self.env[model_name].sudo().browse(line.res_id)
                    if record.exists() and 'partner_id' in record._fields:
                        if record.partner_id and record.partner_id != partner:
                            review_reasons.append(
                                _('%s,%s is linked to a different partner.')
                                % (model_name, line.res_id))
                except Exception:  # noqa: BLE001
                    pass

        return {
            'wizard': wizard,
            'sections': sections,
            'review_reasons': review_reasons,
        }

    @api.model
    def action_generate(self, partner_id, request_id=None):
        partner = self.env['res.partner'].browse(partner_id)
        built = self._build_for_partner(partner)
        body_lines = [
            '<h3>%s</h3>' % _('Personal data held about you'),
            '<p>%s</p>' % _(
                'This response lists the categories of personal data we hold '
                'about you, the purposes, the recipients and the retention '
                'periods. Article 15 of Regulation (EU) 2016/679.'),
        ]
        for section in built['sections']:
            body_lines.append(
                '<p><strong>%s</strong> <span class="text-muted">%s</span></p>'
                % (section['reference'], section.get('inventory', '')))
            if section.get('purpose'):
                body_lines.append('<p>%s: %s</p>' % (_('Purpose'), section['purpose']))
            if section.get('legal_basis'):
                body_lines.append('<p>%s: %s</p>' % (_('Legal basis'), section['legal_basis']))
            if section.get('recipients'):
                body_lines.append('<p>%s: %s</p>' % (_('Recipients'), section['recipients']))
            if section.get('retention'):
                body_lines.append('<p>%s: %s</p>' % (_('Retention'), section['retention']))

        response = self.create({
            'partner_id': partner.id,
            'request_id': request_id,
            'lookup_line_count': len(built['wizard'].line_ids),
            'needs_manual_review': bool(built['review_reasons']),
            'review_reason': '\n'.join(built['review_reasons']) or False,
            'body': ''.join(body_lines),
        })
        if request_id:
            self.env['gdpr.access.request'].browse(request_id).write({
                'lookup_line_count': response.lookup_line_count,
                'state': 'answered',
            })
        return response
