from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta


class GdprAccessRequest(models.Model):
    """A data subject access request (Article 15) and its deadline.

    The deadline is one month from creation, extendable by two months when the
    request is complex (Article 12.3). The extension reason is mandatory when
    an extension is applied — an unexplained extension is not demonstrable.
    """

    _name = 'gdpr.access.request'
    _description = 'GDPR Access Request'
    _inherit = ['mail.thread']
    _order = 'request_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True,
        default=lambda self: _('New'))
    partner_id = fields.Many2one(
        'res.partner', string='Data Subject', required=True, index=True,
        ondelete='cascade')
    request_date = fields.Datetime(
        string='Requested', required=True, default=fields.Datetime.now)
    deadline = fields.Datetime(
        string='Deadline', compute='_compute_deadline', store=True, index=True,
        help='One month from the request, extended by two months when an '
             'extension is applied (Article 12.3).')
    extension_applied = fields.Boolean(
        string='Extended', help='Article 12.3: two further months for complex '
                                'requests. The data subject must be informed '
                                'within the first month.')
    extension_reason = fields.Text(
        string='Reason for Extension',
        help='Required when the request is extended. An unexplained extension '
             'cannot be demonstrated to a supervisory authority.')
    extension_date = fields.Datetime(string='Extended On')
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('answered', 'Answered'),
        ('refused', 'Refused'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='new', required=True, tracking=True)
    outcome = fields.Text(
        string='Outcome', help='What was disclosed, and on what basis.')
    response_document = fields.Binary(
        string='Response Document', attachment=True, copy=False)
    response_filename = fields.Char()
    lookup_line_count = fields.Integer(
        string='Records Found', readonly=True,
        help='Number of records the privacy lookup returned when the request '
             'was answered.')
    is_overdue = fields.Boolean(
        string='Overdue', compute='_compute_is_overdue', search='_search_is_overdue')

    @api.depends('request_date', 'extension_applied', 'extension_date')
    def _compute_deadline(self):
        for request in self:
            if not request.request_date:
                request.deadline = False
                continue
            months = 3 if request.extension_applied else 1
            request.deadline = request.request_date + relativedelta(months=months)

    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for request in self:
            request.is_overdue = bool(
                request.deadline
                and request.deadline < now
                and request.state in ('new', 'in_progress'))

    @api.model
    def _search_is_overdue(self, operator, value):
        if operator not in ('=', '!='):
            return []
        now = fields.Datetime.now()
        overdue = self.search([
            ('deadline', '<', now),
            ('state', 'in', ('new', 'in_progress')),
        ])
        if (operator == '=') == bool(value):
            return [('id', 'in', overdue.ids)]
        return [('id', 'not in', overdue.ids)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'gdpr.access.request') or _('New')
        return super().create(vals_list)

    @api.constrains('extension_applied', 'extension_reason')
    def _check_extension_reason(self):
        for request in self:
            if request.extension_applied and not request.extension_reason:
                raise ValueError(_(
                    'An extension requires a reason: Article 12.3 requires the '
                    'data subject to be informed why.'))

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_refuse(self):
        self.write({'state': 'refused'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_extend(self, reason=None):
        """Extend by two months (Article 12.3).

        The reason is mandatory: an extension the data subject was never told
        the reason for cannot be demonstrated. Passing it here rather than in
        a separate write keeps the constraint and the action consistent.
        """
        if reason is not None:
            self.write({'extension_reason': reason})
        if not self.extension_reason:
            raise ValueError(_(
                'An extension requires a reason: Article 12.3 requires the '
                'data subject to be informed why.'))
        self.write({
            'extension_applied': True,
            'extension_date': fields.Datetime.now(),
        })
