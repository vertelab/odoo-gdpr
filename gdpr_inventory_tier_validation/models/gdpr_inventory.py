from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class GDPRInventory(models.Model):
    _name = "gdpr.inventory"
    _description = "GDPR Inventory"
    _inherit = ['gdpr.inventory','tier.validation']
    _state_from = ["draft"]
    _state_to = ["active","restricted"]
    _tier_validation_manual_config = False

    def set_active(self):
        self.write({"state": "active"})

    def set_draft(self):
        self.write({"state": "draft"})

    def restrict_objects(self):
        self.write({"state": "restricted"})
        super(GDPRInventory,self).restrict_objects()