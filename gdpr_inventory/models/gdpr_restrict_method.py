import logging
from datetime import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models,  fields,  api,  _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

class gdpr_restrict_method(models.Model):
    _name = 'gdpr.restrict_method'
    _description = "Restrict Method"
    _inherit = ['mail.thread']

    name = fields.Char()
    description = fields.Text()
    type = fields.Selection(selection=[('erase', 'Erase'), ('hide', 'Hide'), ('encrypt', 'Encrypt'), ('pseudo', 'Pseudonymisation'), ('manual', 'Manual'), ('code', 'Code')])
    code = fields.Text()

    def restrict_objects(self, inventory, objects):
        self.ensure_one()
        """
        Perform restriction.
        :param inventory: The inventory that the objects belong to.
        :param objects: The GDPR objects (gdpr.object) that should be restricted.
        """
        if self.type == 'encrypt':
            raise UserError(_("The restriction method 'Encrypt' is not implemented. Choose another method for inventory '%s'.") % inventory.name)

        if not objects:
            _logger.info("restrict_objects: nothing to restrict for inventory %s", inventory.name)
            return

        if self.type == 'erase':
            self._restrict_erase(inventory, objects)
        elif self.type == 'hide':
            self._restrict_hide(inventory, objects)
        elif self.type == 'pseudo':
            self._restrict_pseudo(inventory, objects)
        elif self.type == 'manual':
            objects.write({'manual': True})
        elif self.type == 'code':
            safe_eval(inventory.restrict_code, self.get_eval_context(inventory=inventory, objects=objects), mode='exec')
        else:
            raise UserError(_("Unknown restriction method '%s'.") % self.type)

    def _restrict_erase(self, inventory, objects):
        """Erase the records through data_recycle, one GDPR object at a time."""
        recycle_model = inventory._get_recycle_model()
        for gdpr_object in objects:
            record = gdpr_object.object_id
            if not record:
                gdpr_object.restricted = True
                continue
            recycle_model._recycle_gdpr_record(self, inventory, record)
            gdpr_object.restricted = True

    def _restrict_hide(self, inventory, objects):
        """Archive the records by setting active to False."""
        for gdpr_object in objects:
            record = gdpr_object.object_id
            if record and 'active' not in record._fields:
                raise UserError(_("Model %s cannot be hidden because it has no 'active' field.") % record._name)
        for gdpr_object in objects:
            record = gdpr_object.object_id
            if record:
                record.write({'active': False})
            gdpr_object.restricted = True

    def _restrict_pseudo(self, inventory, objects):
        """Overwrite the configured fields on the records with the pseudo values."""
        values = safe_eval(inventory.pseudo_values, self.get_eval_context())
        for field in inventory.fields_ids:
            if field.name not in values:
                values[field.name] = False
        for gdpr_object in objects:
            record = gdpr_object.object_id
            if record:
                record.write(values)
            gdpr_object.restricted = True

    @api.model
    def get_eval_context(self, **kw):
        context = {
            # python libs
            'time': time,
            'datetime': datetime,
            'dateutil': relativedelta,

            # orm
            'env': self.env,
        }
        context.update(kw)
        return context
