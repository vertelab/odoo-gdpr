from odoo import api, fields, models, _


class GdprPrivacyLookup(models.AbstractModel):
    """Logging of a data subject lookup, on the platform's own privacy.log.

    `privacy.lookup.wizard._post_log()` only writes a `privacy.log` entry when
    `execution_details` is non-empty, and the core wizard never sets it. Left
    to the core alone, a lookup therefore leaves no trace. Article 5.2
    (accountability) requires that it does.

    The logic lives here rather than in the controller so that it can be
    tested without an HTTP request context.
    """

    _name = 'gdpr.privacy.lookup'
    _description = 'GDPR Privacy Lookup Logging'

    @api.model
    def log_lookup(self, partner, wizard):
        """Record a lookup in `privacy.log`, anonymised. Idempotent."""
        # `log_id` is a plain Many2one without a default: on a fresh wizard it
        # reads as an empty recordset, not False. Test with `not` so both an
        # empty recordset and False are treated as "not logged yet".
        if wizard.log_id:
            return wizard.log_id
        records_description = ', '.join(
            '%s (%s)' % (line.res_model, line.res_id)
            for line in wizard.line_ids
        ) or _('No records found.')
        log = self.env['privacy.log'].sudo().create({
            'anonymized_name': partner.name or '',
            'anonymized_email': partner.email or '',
            'execution_details': _(
                'Data subject access: %s records found.'
            ) % len(wizard.line_ids),
            'records_description': records_description,
        })
        wizard.log_id = log
        return log

    @api.model
    def run_for_partner(self, partner, log=True):
        """Run the platform lookup for one partner and optionally log it.

        Returns the wizard. The search itself is the platform's
        `privacy.lookup.wizard` — this method does not search for personal
        data on its own.
        """
        wizard = self.env['privacy.lookup.wizard'].sudo().create({
            'name': partner.name or '',
            'email': partner.email or '',
        })
        wizard.action_lookup()
        if log:
            self.log_lookup(partner, wizard)
        return wizard
