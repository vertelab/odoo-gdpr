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

        list_partners = objects.mapped('partner_id')
        model = list_partners[0]
        list_partner_ids = [o.id for o in list_partners]
        partner_ids = model.browse(list_partner_ids)

        # I have extracted the strings to be used for the message so they can be properly translated.
        # first_msg_part = _("The following action")
        # second_msg_part = _("was applyed to this/these records:")

        # name_and_ids = [f"(name: {o.name if hasattr(o,'name') else _('No Name')} | id: {o.id})" for o in list_objects]
        # message = f"{first_msg_part} '{self.type}' {second_msg_part} {', '.join(name_and_ids)}"

        if self.type == 'erase':
            partner_ids.unlink()
            objects.unlink()
        elif self.type == 'hide':
            if hasattr(model, 'active'):
                partner_ids.write({'active': False})
                objects.write({'restricted': True})
        elif self.type == 'encrypt':
            pass
        elif self.type == 'pseudo':
            values = safe_eval(inventory.pseudo_values, self.get_eval_context())
            for field in inventory.fields_ids:
                if field.name not in values:
                    values[field.name] = False
            partner_ids.write(values)
            objects.write({'restricted': True})
        elif self.type == 'manual':
            objects.write({'manual': True})
            # TODO: Button to list expired records.
        elif self.type == 'code':
            safe_eval(inventory.restrict_code, self.get_eval_context(inventory=inventory, objects=objects), mode='exec')

        self.env["gdpr.log"].create({
            "inventory_id": inventory.id,
            "responsible": inventory.user_id.id,
            "restriction_domain": inventory.restrict_domain,
            "restriction_method": self.type
        })

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