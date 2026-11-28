import logging

from odoo import models,  fields,  api,  _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    consent_ids = fields.One2many(comodel_name='gdpr.consent', compute='_compute_consent_ids')

    @api.depends('res_model', 'res_id')
    def _compute_consent_ids(self):
        for rec in self:
            if isinstance(rec.id, int):
                rec.consent_ids = self.env['gdpr.consent'].search([('gdpr_object_id.object_id', '=', '%s,%s' % (rec._name, rec.id),)])
            else:
                rec.consent_ids = False
