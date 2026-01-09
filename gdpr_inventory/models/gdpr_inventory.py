import logging

from odoo import models,  fields,  api,  _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

common_eval_vars = """
Available variables:
* env: Odoo environment.
* time: time python module.
* datetime: datetime python module.
* dateutil: dateutil python module.
* timezone: pytz.timezone python module."""

class gdpr_inventory(models.Model):
    _name = 'gdpr.inventory'
    _description = 'GDPR Inventory'
    _inherit = ['mail.thread']

    @api.model
    def _default_system_id(self):
        return self.env.ref('gdpr_inventory.gdpr_system_odoo', False)

    @api.model
    def _default_subject_ids(self):
        return self.env.ref('gdpr_inventory.gdpr_data_subject_customer', False)
    
    # @api.model
    # def _default_state_id(self):
    #     return self.env['gdpr.inventory.state'].search([], order='sequence', limit=1)

    def consent_get(self, partner=None, object=None):
        return self.env['gdpr.consent'].get_consent(self, partner, object)

    name = fields.Char(string="Name", translate=True, required=True)
    color = fields.Integer(string='Color Index')
    # state_id = fields.Many2one(comodel_name='gdpr.inventory.state', default=_default_state_id, string='State', group_expand='_expand_stages')
    state = fields.Selection(selection=[("draft","Draft"),("active","Active"),("ceased","Ceased")], default="draft")
    type_of_personal_data = fields.Selection(selection=[('general', 'General'), ('special', 'Special Category'), ('child', 'Childs consent'), ('criminal', 'Criminal related')], string="Type",
         help="General: non sensitive personal data,   Special: sensitive personal data,  Child consent: personal data concerning under aged persons,  Criminal relared:  personal data relating to criminal convictions and offences")
    role = fields.Selection(selection=[('controller', 'Controller'), ('processor', 'Processor')], string='Our Role', default='controller', required=True, track_visibility='onchange')
    category = fields.Many2one(comodel_name="gdpr.category", string="Category", required=True,help="Divide inventories in several catories eg Customers, Resellers etc")
    business_process = fields.Many2one(comodel_name="gdpr.bp", string="Business Process", help="Attach the inventorie to a business process")
    user_id = fields.Many2one(comodel_name="res.users", string="Responsible", track_visibility='onchange', required=True)
    parent_id = fields.Many2one(comodel_name="gdpr.inventory")
    partner_fields_ids = fields.Many2many(comodel_name="ir.model.fields", string="Partner Fields", relation='gdpr_inventory_ir_model_rel_partner_fields_ids', help="Fields with personal link")
    partner_domain = fields.Text(string="Partner Domain", help="Domain for identification of partners connected to this personal data")
    partner_ids = fields.Many2many(string='Partners', comodel_name='res.partner', compute='_partner_ids', store=True)
    partner_count = fields.Integer(string='Partner Count', compute='_partner_ids', store=True)
    object_ids = fields.One2many(string='Objects', comodel_name='gdpr.object', inverse_name='gdpr_id')
    object_count = fields.Integer(string='Object Count', compute='_object_count', store=True)
    security_of_processing_ids = fields.Many2many(comodel_name="gdpr.security", string="Security", help="Security of processing", track_visibility='onchange')
    log_ids = fields.One2many(comodel_name="gdpr.log",inverse_name="inventory_id")
    log_count = fields.Integer(compute="_compute_log_count")

    # Identification
    identification_desc = fields.Text(string='Identification Description', track_visibility='onchange', translate=True, help="A description of how the data items covered by this inventory can be identified.")
    data_local = fields.Boolean(string='Data Is Local', help="The data is stored in this Odoo database and should be automatically inventoried.")
    inventory_model = fields.Many2one(comodel_name="ir.model", string="Inventory Model",  help="Model (Class) for this Inventory")
    inventory_domain = fields.Text(string="Inventory Domain", help="Domain for identification of personal data of this type\n%s" % common_eval_vars, default='[]')
    inventory_domain_advanced = fields.Boolean(string='Advanced Domain')
    inventory_domain_code = fields.Text(string='Restrict Domain Code', help="Python code that will be executed before domain evaluation. Any variables defined here will be available during domain evaluation.\n%s\n* restrict_days: Restrict time of this inventory" % common_eval_vars)

    # Purpose
    purpose_limitation = fields.Text(track_visibility='onchange', translate=True, required=True)
    lawsection_desc = fields.Html(string="Law section Explanation", track_visibility='onchange',translate=True)
    lawsection_id = fields.Many2one(comodel_name="gdpr.lawsection", string="Law Section", required=True, track_visibility='onchange')
    lawsection_description = fields.Html(related='lawsection_id.description', readonly=True, track_visibility='onchange')
    consent = fields.Boolean(related='lawsection_id.consent', track_visibility='onchange')

    # Data description
    data_subject_ids = fields.Many2many(comodel_name='gdpr.subject', string='Data Subjects', default=_default_subject_ids, track_visibility='onchange')
    data_type_ids = fields.Many2many(comodel_name='gdpr.data_type', string='Data Types', help="A description of the types of data that are stored in this inventory.", track_visibility='onchange')
    data_collection_ids = fields.Many2many(comodel_name='gdpr.system', string='Data Collection', relation='gdpr_inventory_gdpr_system_collection_rel', column1='gdpr_id', column2='system_id', help="The system that is used to collect data for this inventory.", default=_default_system_id, track_visibility='onchange')
    data_storage_ids = fields.Many2many(comodel_name='gdpr.system', string='Data Storage', relation='gdpr_inventory_gdpr_system_storage_rel', column1='gdpr_id', column2='system_id', help="The system that is used to store data for this inventory.", default=_default_system_id, track_visibility='onchange')
    data_sharing_ids = fields.Many2many(comodel_name='res.partner', relation='gdpr_inventory_res_partner_sharing_rel', column1='gdpr_id', column2='partner_id', string='Data Sharing', help="Any partners that we share this data with.", track_visibility='onchange')

    # Consent
    consent_title = fields.Char(string="Title")
    consent_desc = fields.Text(string="Description")
    consent_ids = fields.One2many(comodel_name='gdpr.consent', inverse_name='gdpr_id', string='Consents')
    consent_count = fields.Integer(string='Consent Count', compute='_consent_count', store=True)

    # Restrictions
    restrict_desc = fields.Text(string='Restriction Description', track_visibility='onchange', translate=True, help="A description of how the data items covered by this inventory can be identified.")
    restrict_scheduled_time = fields.Date(help="Time when the restriction will be applied")
    # restrict_time_days = fields.Integer(string='Restrict time', help="Number of days before this data will be restricted", track_visibility='onchange')
    restrict_method_id = fields.Many2one(comodel_name="gdpr.restrict_method", string="Restrict Method", track_visibility='onchange')
    restrict_domain = fields.Text(string='Restrict Domain', help="Domain for identifying records that should be restricted.\n%s\n* restrict_days: Restrict time of this inventory" % common_eval_vars, default='[]')
    restrict_domain_advanced = fields.Boolean(string='Advanced Domain')
    restrict_domain_code = fields.Text(string='Restrict Domain Code', help="Python code that will be executed before domain evaluation. Any variables defined here will be available during domain evaluation.\n%s" % common_eval_vars)
    restrict_code = fields.Text(string='Restriction Code', help="""Python code to run when restricting records.
%s
* inventory: This inventory record.
* objects: The gdpr objects to be restricted (gdpr.object). Actual records to be processed can be accessed through objects.mapped('object_id').""" % common_eval_vars, default = '{}')
    pseudo_values = fields.Text(string='Pseudonymisation Values', help="Custom values used to anonymize fields. Any fields not specified in this dict will be set to False.", default = '{}')
    restrict_type = fields.Selection(string='Restriction Type', related='restrict_method_id.type')
    manual_count = fields.Integer(string='Manual Count', compute='_manual_count', default=0)
    fields_ids = fields.Many2many(comodel_name="ir.model.fields", string="Fields", relation='gdpr_inventory_ir_model_rel_fields_ids', help="Fields with (potential) personal data")

    @api.depends('object_ids','object_ids.object_id')
    def _object_count(self):
        self.ensure_one()
        self.object_count = len(self.object_ids.mapped('object_id'))

    @api.depends('consent_ids')
    def _consent_count(self):
        self.ensure_one()
        self.consent_count = len(self.consent_ids)

    @api.depends('object_ids','object_ids.partner_id')  
    def _partner_ids(self):
        self.ensure_one()
        self.partner_ids = self.object_ids.mapped('partner_id')
        self.partner_count = len(self.partner_ids)

    @api.onchange('restrict_method_id')
    def onchange_restrict_method_id(self):
        if self.restrict_method_id:
            self.restrict_code = self.restrict_method_id.code

    @api.onchange('restrict_method_id', 'inventory_model')
    def onchange_verify_hide(self):
        if self.restrict_method_id and self.restrict_method_id.type == 'hide' and self.inventory_model:
            if not self.env['ir.model.fields'].search_count([('model_id', '=', self.inventory_model.id), ('name', '=', 'active')]):
                raise UserError("Model %s (%s) can not be hidden because it does not have an 'active' field." % (self.inventory_model.name, self.inventory_model.model))

    def _expand_stages(self, stages, domain):
        return self.env['gdpr.inventory.state'].search([])

    def _manual_count(self):
        self.ensure_one()
        self.manual_count = self.env['gdpr.object'].search_count([('manual', '=', True), ('restricted', '=', False), ('gdpr_id', '=', self.id)])
    
    def _compute_log_count(self):
        for rec in self:
            rec.log_count = len(rec.log_ids)

    def action_view_objects(self):
        object_ids = self.object_ids.mapped("object_id")
        ids = [o.id for o in object_ids if hasattr(o, 'id')]
        return {
            'type': u'ir.actions.act_window',
            'target': u'current',
            'res_model': self.inventory_model.model,
            'view_mode': u'list,form',
            'domain': [('id', 'in', ids)],
        }
    
    def action_view_manual_objects(self):
        return {
            'type': u'ir.actions.act_window',
            'target': u'current',
            'res_model': 'gdpr.object',
            'view_mode': u'list,form',
            'domain': [('gdpr_id', '=', self.id)],
            'context': {'search_default_manual': 1, 'search_default_unrestricted': 1},
        }
    
    def action_view_logs(self):
        return {
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_model': 'gdpr.log',
            'view_mode': 'list,form',
            'domain': [('inventory_id', '=', self.id)],
            # 'context': {'search_default_manual': 1, 'search_default_unrestricted': 1},
        }
    
    def act_gdpr_inventory_2_gdpr_res_partner(self):
        return {
            'name': 'Res Partner 2 GDPR Inventory Partner',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,list,form',
            'view_type': 'kanban',
            'domain': [('id', 'in', self.partner_ids.mapped('id'))],
            'context': {},
        }

    def update_partner_ids(self):
        self.ensure_one()
        """Update partner_ids field."""
        pass

    def update_object_ids(self):
        self.ensure_one()
        if not self.data_local:
            return
        # Remove non-existing objects
        model = self.env[self.inventory_model.model]
        if model.fields_get('active'):
            object_ids = [d['id'] for d in model.search_read([('active', 'in', (True, False))], ['id'])]
        else:
            object_ids = [d['id'] for d in model.search_read([], ['id'])]
        self.env['gdpr.object'].search([('gdpr_id', '=', self.id), ('object_res_id', 'not in', object_ids)]).unlink()

        # Update all matching objects
        global_vars = self.env['gdpr.restrict_method'].get_eval_context()        
        objects = model.search(safe_eval(self.inventory_domain, global_vars))
        for o in self.object_ids:
            if o.object_id:
                objects |= o.object_id
        for o in objects:
            partners = self.env['res.partner'].browse([])
            for p in self.partner_fields_ids:
                if p.ttype == 'integer' and getattr(o, p.name):
                    # Assume that this is the ID of a partner
                    partners |= self.env['res.partner'].browse(getattr(o, p.name))
                else:
                    partners |= getattr(o, p.name)
            for partner in partners:
                if not self.env['gdpr.object'].search([('gdpr_id', '=', self.id), ('object_id', '=', '%s,%s' %(self.inventory_model.model, o.id)), ('partner_id', '=', partner.id)]):
                    self.env['gdpr.object'].create({
                        'gdpr_id': self.id,
                        'object_id': '%s,%s' %(o._name, o.id),
                        'partner_id': partner.id,
                    })

    def restrict_objects(self):

        self.ensure_one()
        """
        Check if any records meet the restrict critera and perform restriction according to the chosen restrict method.
        """

        if not self.env.user.has_group("gdpr_inventory.group_gdpr_officer"):
            raise AccessError(_("Only GDPR Officers can perform this operation. Please contact your system administrator if you believe this is an error."))

        if self.data_local and self.restrict_method_id:
            model = self.inventory_model.model
            global_vars = self.env['gdpr.restrict_method'].get_eval_context(restrict_days=self.restrict_scheduled_time)
            domain = safe_eval(self.restrict_domain, global_vars)
            object_ids = [o['id'] for o in self.env[model].search_read(domain, ['id'])]
            _logger.debug('restrict_objects object_ids: %s' % object_ids)
            domain = [('restricted', '!=', True), ('gdpr_id', '=', self.id), ('object_res_id', 'in', object_ids)]
            if self.lawsection_id.consent:
                gdpr_o_ids = [o['gdpr_object_id'][0] for o in self.env['gdpr.consent'].search_read([('state', '=', 'withdrawn'), ('record_id', 'in', [('%s,%s' % (model, id)) for id in object_ids]), ('gdpr_id', '=', self.id)], ['gdpr_object_id'])]
                domain.append(('id', 'in', gdpr_o_ids))
            _logger.debug('restrict_objects domain: %s' % domain)
            objects = self.env['gdpr.object'].search(domain)
            if objects:
                self.restrict_method_id.restrict_objects(self, objects)

    @api.model
    def cron(self):
        gdpr_inventory_ids = self.env["gdpr.inventory"].search([("state","=","active")])
        for gdpr_inventory_id in gdpr_inventory_ids:
            gdpr_inventory_id.update_object_ids()
            gdpr_inventory_id.restrict_objects()

    @api.model
    def _read_state_id(self, present_ids, domain, **kwargs):
        states = self.env['gdpr.inventory.state'].search([], order='sequence').name_get()
        return states, None
    @api.model
    def _read_lawsection_id(self, present_ids, domain, **kwargs):
        return self.env['gdpr.lawsection'].search([], order='sequence').name_get(), None
    @api.model
    def _read_business_process(self, present_ids, domain, **kwargs):
        return self.env['gdpr.bp'].search([], order='sequence').name_get(), None
    @api.model
    def _read_role(self, present_ids, domain, **kwargs):
        return self.env['gdpr.role'].search([], ).name_get(), None
    @api.model
    def _read_category(self, present_ids, domain, **kwargs):
        return self.env['gdpr.category'].search([], order='sequence').name_get(), None
    @api.model
    def _read_user_id(self, present_ids, domain, **kwargs):
        return self.env['gdpr.inventory'].search([], ).mapped('user_id').name_get(), None
    @api.model
    def _read_restrict_method_id(self, present_ids, domain, **kwargs):
        return self.env['gdpr.restrict_method'].search([], ).name_get(), None
    @api.model
    def _read_type(self, present_ids, domain, **kwargs):
        return [('general', 'General'), ('special', 'Special Category'), ('child', 'Childs consent'), ('criminal', 'Criminal related')], None
    _group_by_full = {
        'state_id': _read_state_id,
        'lawsection_id': _read_lawsection_id,
        'business_process': _read_business_process,
        'role': _read_role,
        'category': _read_category,
        'user_id': _read_user_id,
        'restrict_method_id': _read_restrict_method_id,
    }