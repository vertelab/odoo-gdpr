import logging

from odoo import models,  fields,  api,  _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _consent_ids(self):
        self.ensure_one()
        if type(self.id) == int:
            self.consent_ids = self.env['gdpr.consent'].search([('gdpr_object_id.object_id', '=', '%s,%s' % (self._name, self.id),)])
    consent_ids = fields.One2many(comodel_name='gdpr.consent', compute='_consent_ids')
