import logging

from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DataRecycleModel(models.Model):
    _inherit = 'data_recycle.model'

    def _recycle_gdpr_record(self, restrict_method, inventory, record):
        """Erase or archive a single record through data_recycle.

        The rule is created from the inventory's domain, so the record must also
        match that domain. A record that does not match is not touched.
        """
        self.ensure_one()
        if record._name != self.res_model_name:
            raise UserError(_("Record %(record)s belongs to %(model)s, but the recycle rule for inventory '%(inventory)s' is for %(rule_model)s.",
                              record=record.display_name, model=record._name,
                              inventory=inventory.name, rule_model=self.res_model_name))
        recycle_record = self.env['data_recycle.record'].create({
            'recycle_model_id': self.id,
            'res_id': record.id,
        })
        recycle_record.action_validate()
        _logger.info('_recycle_gdpr_record: %s %s (%s) handled by %s for inventory %s',
                     self.recycle_action, record._name, record.id, restrict_method.type, inventory.name)
