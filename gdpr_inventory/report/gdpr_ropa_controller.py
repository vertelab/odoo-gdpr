from odoo import http
from odoo.http import request, content_disposition


class GdprRopaController(http.Controller):
    """CSV download of the Article 30 register.

    The register is also available as PDF through the report action. CSV is a
    separate route because the file must carry a BOM for Excel to read the
    semicolon-separated UTF-8 correctly.
    """

    @http.route('/gdpr/ropa.csv', type='http', auth='user')
    def ropa_csv(self, **kw):
        if not request.env.user.has_group('gdpr_inventory.group_gdpr_officer'):
            return request.not_found()
        report = request.env['report.gdpr_inventory.gdpr_ropa_report']
        body = report._csv_bytes()
        report._log_generation(
            request.env['gdpr.inventory'].search_count([('state', '=', 'active')]))
        return request.make_response(
            body,
            headers=[
                ('Content-Type', 'text/csv; charset=utf-8'),
                ('Content-Disposition',
                 content_disposition('gdpr-article-30-register.csv')),
            ],
        )
