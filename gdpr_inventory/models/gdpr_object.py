import logging

from odoo import models,  fields,  api,  _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

class gdpr_object(models.Model):
    _name = 'gdpr.object'

    name = fields.Char(string='Name', compute='_compute_name')
    gdpr_id = fields.Many2one(string='Inventory', comodel_name='gdpr.inventory')
    object_id = fields.Reference(string='Object', selection='_reference_models', compute='_get_object_id', inverse='_set_object_id', search='_search_object_id')
    object_model = fields.Char(string='Object Model')
    object_res_id = fields.Integer(string='Object ID')
    partner_id = fields.Many2one(string='Partners', comodel_name='res.partner')
    restricted = fields.Boolean(string='Restricted', help="This record has been restricted.")
    manual = fields.Boolean(string='Manual Action Required', help="This record needs attention.")

    def _compute_name(self):
        for rec in self:
            if rec.object_id and hasattr(rec.object_id, 'name'):
                rec.name = rec.object_id.name
            elif rec.object_id:
                rec.name = '%s, %s' % (rec.object_id._name, rec.object_id.id)
            else:
                rec.name = 'gdpr.object, %s' % rec.id

    def _get_object_id(self):
        for rec in self:
            if rec.object_model and rec.object_res_id:
                rec.object_id = self.env[rec.object_model].search([('id', '=', rec.object_res_id)])

    def _set_object_id(self):
        for rec in self:
            if rec.object_id:
                rec.object_res_id = rec.object_id.id
                rec.object_model = rec.object_id._name
            else:
                rec.object_res_id = False
                rec.object_model = False

    @api.model
    def _search_object_id(self, operator, value):
        _logger.debug('_search_object_id; operator: %s, value: %s' % (operator, value))
        if operator in ('in', 'not in'):
            if operator == 'in':
                op_m = '='
                ao1 = '&'
                ao2 = '|'
            else:
                op_m = '!='
                ao1 = '|'
                ao2 = '&'
            ids = {}
            for v in value:
                m, id = v.split(',')
                if m not in ids:
                    ids[m] = []
                ids[m].append(int(id))
            res = []
            for model in ids:
                if res:
                    res = [ao2] + res
                res += [ao1, ('object_model', op_m, model), ('object_res_id', operator, ids[model])]
        elif value:
            res = ['&', ('object_model', operator, value.split(',')[0]), ('object_res_id', operator, int(value.split(',')[1]))]
        else:
            res = ['&', ('object_model', operator, value), ('object_res_id', operator, value)]
        _logger.debug(res)
        return res

    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].search([('state', '!=', 'manual')])
        return [(model.model, model.name) for model in models]