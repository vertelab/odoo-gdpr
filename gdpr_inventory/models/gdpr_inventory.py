import logging

from dateutil.relativedelta import relativedelta

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
    role = fields.Selection(selection=[('controller', 'Controller'), ('processor', 'Processor')], string='Our Role', default='controller', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Controller',
        default=lambda self: self.env.company, required=True, index=True,
        help='The legal entity that is the controller of this processing. '
             'Article 30.1(a) requires it to be recorded.')
    category = fields.Many2one(comodel_name="gdpr.category", string="Category", required=True,help="Divide inventories in several catories eg Customers, Resellers etc")
    business_process = fields.Many2one(comodel_name="gdpr.bp", string="Business Process", help="Attach the inventorie to a business process")
    user_id = fields.Many2one(comodel_name="res.users", string="Responsible", tracking=True, required=True)
    parent_id = fields.Many2one(comodel_name="gdpr.inventory")
    partner_fields_ids = fields.Many2many(comodel_name="ir.model.fields", string="Partner Fields", relation='gdpr_inventory_ir_model_rel_partner_fields_ids', help="Fields with personal link")
    partner_domain = fields.Text(string="Partner Domain", help="Domain for identification of partners connected to this personal data")
    partner_ids = fields.Many2many(string='Partners', comodel_name='res.partner', compute='_partner_ids', store=True)
    partner_count = fields.Integer(string='Partner Count', compute='_partner_ids', store=True)
    object_ids = fields.One2many(string='Objects', comodel_name='gdpr.object', inverse_name='gdpr_id')
    object_count = fields.Integer(string='Object Count', compute='_object_count', store=True)
    security_of_processing_ids = fields.Many2many(comodel_name="gdpr.security", string="Security", help="Security of processing", tracking=True)
    log_ids = fields.One2many(comodel_name="gdpr.log",inverse_name="inventory_id")
    log_count = fields.Integer(compute="_compute_log_count")

    # Identification
    identification_desc = fields.Text(string='Identification Description', tracking=True, translate=True, help="A description of how the data items covered by this inventory can be identified.")
    data_local = fields.Boolean(string='Data Is Local', help="The data is stored in this Odoo database and should be automatically inventoried.")
    inventory_model = fields.Many2one(comodel_name="ir.model", string="Inventory Model",  help="Model (Class) for this Inventory")
    inventory_domain = fields.Text(string="Inventory Domain", help="Domain for identification of personal data of this type\n%s" % common_eval_vars, default='[]')
    inventory_domain_advanced = fields.Boolean(string='Advanced Domain')
    inventory_domain_code = fields.Text(string='Restrict Domain Code', help="Python code that will be executed before domain evaluation. Any variables defined here will be available during domain evaluation.\n%s\n* restrict_days: Restrict time of this inventory" % common_eval_vars)

    # Purpose
    purpose_limitation = fields.Text(tracking=True, translate=True, required=True)
    purpose_id = fields.Many2one(comodel_name="gdpr.lawsection", string="Purpose / Legal basis", tracking=True, help="The legal basis this processing activity relies on. Carried in the context as 'gdpr_purpose_id' so drill-downs and the purpose indicator stay scoped to the same purpose.")
    lawsection_desc = fields.Html(string="Law section Explanation", tracking=True,translate=True)
    lawsection_id = fields.Many2one(comodel_name="gdpr.lawsection", string="Law Section", required=True, tracking=True)
    lawsection_description = fields.Html(related='lawsection_id.description', readonly=True, tracking=True)
    consent = fields.Boolean(related='lawsection_id.consent', tracking=True)

    # Article 30
    dpo_partner_id = fields.Many2one(comodel_name='res.partner', string='Data Protection Officer', tracking=True, help="The data protection officer responsible for this processing activity.")
    recipient_category_ids = fields.Many2many(comodel_name='gdpr.recipient_category', string='Recipient Categories', tracking=True, help="Categories of recipients to whom the personal data are disclosed.")
    third_country_ids = fields.Many2many(comodel_name='res.country', string='Third Countries', tracking=True, help="Third countries or international organisations to which personal data are transferred.")
    transfer_safeguards = fields.Text(string='Transfer Safeguards', tracking=True, translate=True, help="Safeguards for transfers to third countries, e.g. standard data protection clauses (Art. 46).")
    retention_months = fields.Integer(string='Retention (Months)', tracking=True, help="Number of months the personal data may be stored, counted from the creation of this inventory.")
    retention_date = fields.Date(string='Retention Date', compute='_compute_retention_date', store=True, help="Date when the retention period expires.")

    # Data description
    data_subject_ids = fields.Many2many(comodel_name='gdpr.subject', string='Data Subjects', default=_default_subject_ids, tracking=True)
    data_type_ids = fields.Many2many(comodel_name='gdpr.data_type', string='Data Types', help="A description of the types of data that are stored in this inventory.", tracking=True)
    data_collection_ids = fields.Many2many(comodel_name='gdpr.system', string='Data Collection', relation='gdpr_inventory_gdpr_system_collection_rel', column1='gdpr_id', column2='system_id', help="The system that is used to collect data for this inventory.", default=_default_system_id, tracking=True)
    data_storage_ids = fields.Many2many(comodel_name='gdpr.system', string='Data Storage', relation='gdpr_inventory_gdpr_system_storage_rel', column1='gdpr_id', column2='system_id', help="The system that is used to store data for this inventory.", default=_default_system_id, tracking=True)
    data_sharing_ids = fields.Many2many(comodel_name='res.partner', relation='gdpr_inventory_res_partner_sharing_rel', column1='gdpr_id', column2='partner_id', string='Data Sharing', help="Any partners that we share this data with.", tracking=True)

    # Consent
    consent_title = fields.Char(string="Title")
    consent_desc = fields.Text(string="Consent Description")
    consent_ids = fields.One2many(comodel_name='gdpr.consent', inverse_name='gdpr_id', string='Consents')
    consent_count = fields.Integer(string='Consent Count', compute='_consent_count', store=True)

    # Restrictions
    restrict_desc = fields.Text(string='Restriction Description', tracking=True, translate=True, help="A description of how the data items covered by this inventory can be identified.")
    restrict_scheduled_time = fields.Date(help="Time when the restriction will be applied")
    # restrict_time_days = fields.Integer(string='Restrict time', help="Number of days before this data will be restricted", tracking=True)
    restrict_method_id = fields.Many2one(comodel_name="gdpr.restrict_method", string="Restrict Method", tracking=True)
    restrict_domain = fields.Text(string='Restrict Domain', help="Domain for identifying records that should be restricted.\n%s\n* restrict_days: Restrict time of this inventory" % common_eval_vars, default='[]')
    restrict_domain_advanced = fields.Boolean(string='Advanced Domain')
    restrict_domain_code = fields.Text(string='Restrict Domain Code', help="Python code that will be executed before domain evaluation. Any variables defined here will be available during domain evaluation.\n%s" % common_eval_vars)
    restrict_code = fields.Text(string='Restriction Code', help="""Python code to run when restricting records.
%s
* inventory: This inventory record.
* objects: The gdpr objects to be restricted (gdpr.object). Actual records to be processed can be accessed through objects.mapped('object_id').""" % common_eval_vars, default = '{}')
    pseudo_values = fields.Text(string='Pseudonymisation Values', help="Custom values used to anonymize fields. Any fields not specified in this dict will be set to False.", default = '{}')
    restrict_type = fields.Selection(string='Restriction Type', related='restrict_method_id.type')
    dry_run = fields.Boolean(string='Dry Run', default=True, tracking=True, help="When checked, the restriction only reports what would happen. No records are erased, hidden or pseudonymised.")
    recycle_model_id = fields.Many2one(comodel_name='data_recycle.model', string='Recycle Model', readonly=True, copy=False, help="The data_recycle rule generated from this inventory when it was activated.")
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

    @api.depends('create_date', 'retention_months')
    def _compute_retention_date(self):
        for rec in self:
            if rec.create_date and rec.retention_months:
                rec.retention_date = rec.create_date.date() + relativedelta(months=rec.retention_months)
            else:
                rec.retention_date = False

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

    def _get_purpose_context(self):
        """Context that carries this inventory's purpose into drill-down actions."""
        self.ensure_one()
        return {'gdpr_purpose_id': self.purpose_id.id}

    def action_view_objects(self):
        object_ids = self.object_ids.mapped("object_id")
        ids = [o.id for o in object_ids if hasattr(o, 'id')]
        return {
            'type': u'ir.actions.act_window',
            'target': u'current',
            'res_model': self.inventory_model.model,
            'view_mode': u'list,form',
            'domain': [('id', 'in', ids)],
            'context': self._get_purpose_context(),
        }
    
    def action_view_manual_objects(self):
        return {
            'type': u'ir.actions.act_window',
            'target': u'current',
            'res_model': 'gdpr.object',
            'view_mode': u'list,form',
            'domain': [('gdpr_id', '=', self.id)],
            'context': dict(self._get_purpose_context(), search_default_manual=1, search_default_unrestricted=1),
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
            'context': self._get_purpose_context(),
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

    def _get_recycle_model(self):
        """Return the data_recycle rule for this inventory, creating or updating it."""
        self.ensure_one()
        recycle_action = 'archive' if self.restrict_type == 'hide' else 'unlink'
        values = {
            'name': _('GDPR: %s') % self.name,
            'res_model_id': self.inventory_model.id,
            'domain': self.restrict_domain or '[]',
            'recycle_mode': 'automatic' if not self.dry_run else 'manual',
            'recycle_action': recycle_action,
            'notify_user_ids': [(6, 0, self.user_id.ids)],
        }
        if self.recycle_model_id:
            self.recycle_model_id.write(values)
        else:
            self.recycle_model_id = self.env['data_recycle.model'].create(values)
        return self.recycle_model_id

    def _get_restrict_objects(self):
        """Return the gdpr.object records that match the restriction criteria."""
        self.ensure_one()
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
        return self.env['gdpr.object'].search(domain)

    def _log_restriction(self):
        """Write the gdpr.log entry for a restriction, before the restriction runs."""
        self.ensure_one()
        return self.env['gdpr.log'].create({
            'inventory_id': self.id,
            'responsible': self.user_id.id,
            'restriction_domain': self.restrict_domain,
            'restriction_method': self.restrict_type,
        })

    def restrict_objects(self):

        self.ensure_one()
        """
        Check if any records meet the restrict critera and perform restriction according to the chosen restrict method.
        """

        if not self.env.user.has_group("gdpr_inventory.group_gdpr_officer"):
            raise AccessError(_("Only GDPR Officers can perform this operation. Please contact your system administrator if you believe this is an error."))

        if not (self.data_local and self.restrict_method_id):
            return
        if self.restrict_type == 'encrypt':
            raise UserError(_("The restriction method 'Encrypt' is not implemented. Choose another method for inventory '%s'.") % self.name)

        objects = self._get_restrict_objects()
        if not objects:
            _logger.info('restrict_objects: no objects to restrict for inventory %s', self.name)
            return

        if self.dry_run:
            _logger.info('restrict_objects: dry run for inventory %s, %s objects would be restricted with %s: %s',
                         self.name, len(objects), self.restrict_type, objects.mapped('object_res_id'))
            return

        # Flag the objects and log the restriction before anything is changed, so an
        # interrupted run can be inspected and resumed instead of leaving half a batch.
        objects.write({'restricted': True})
        self._log_restriction()
        self.env.cr.commit()

        failed = self.env['gdpr.object']
        for gdpr_object in objects:
            try:
                with self.env.cr.savepoint():
                    self.restrict_method_id.restrict_objects(self, gdpr_object)
            except Exception as e:
                failed |= gdpr_object
                _logger.exception('restrict_objects: failed to restrict %s (%s, %s): %s',
                                  gdpr_object.name, gdpr_object.object_model, gdpr_object.object_res_id, e)
        if failed:
            _logger.warning('restrict_objects: %s of %s objects failed for inventory %s', len(failed), len(objects), self.name)

    @api.model
    def _cron_restrict(self):
        gdpr_inventory_ids = self.env["gdpr.inventory"].search([("state","=","active")])
        for gdpr_inventory_id in gdpr_inventory_ids:
            try:
                with self.env.cr.savepoint():
                    gdpr_inventory_id.update_object_ids()
                    gdpr_inventory_id.restrict_objects()
            except Exception as e:
                _logger.exception('_cron_restrict: inventory %s (%s) failed: %s', gdpr_inventory_id.name, gdpr_inventory_id.id, e)

    @api.model
    def cron(self):
        self._cron_restrict()
