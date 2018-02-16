(function() {

var instance = openerp;

FieldCharDomainGDPR = instance.web.form.FieldCharDomain.extend({
    on_click: function(event) {
        event.preventDefault();
        var self = this;
        var model = this.options.model || this.field_manager.get_field_value(this.options.model_field);
        this.pop = new instance.web.form.SelectCreatePopup(this);
        var domain = [];
        var gdpr_domain_field = this.options['gdpr_domain_field'];
        console.log(gdpr_domain_field);
        if (gdpr_domain_field !== undefined) {
            domain = instance.web.pyeval.eval('domain', this.getParent().fields[gdpr_domain_field].get_value());
        };
        if(this.get('effective_readonly')) {
            domain = instance.web.pyeval.eval('domain', self.get_value());
        }
        this.pop.select_element(
            model, {
                title: this.get('effective_readonly') ? 'Selected records' : 'Select records...',
                readonly: this.get('effective_readonly'),
                disable_multiple_selection: this.get('effective_readonly'),
                no_create: this.get('effective_readonly'),
            }, domain, this.build_context());
        this.pop.on("elements_selected", self, function(element_ids) {
            if (this.pop.$('input.oe_list_record_selector').prop('checked')) {
                var search_data = this.pop.searchview.build_search_data();
                var domain_done = instance.web.pyeval.eval_domains_and_contexts({
                    domains: search_data.domains,
                    contexts: search_data.contexts,
                    group_by_seq: search_data.groupbys || []
                }).then(function (results) {
                    return results.domain;
                });
            }
            else {
                var domain = [["id", "in", element_ids]];
                var domain_done = $.Deferred().resolve(domain);
            }
            $.when(domain_done).then(function (domain) {
                var domain = self.pop.dataset.domain.concat(domain || []);
                self.set_value(domain);
            });
        });
    },
});

instance.web.form.FieldCharDomain = FieldCharDomainGDPR;

/**
 * Registry of form fields, called by :js:`instance.web.FormView`.
 *
 * All referenced classes must implement FieldInterface. Those represent the classes whose instances
 * will substitute to the <field> tags as defined in OpenERP's views.
 */
instance.web.form.widgets = instance.web.form.widgets.extend({
    'char_domain': 'instance.web.form.FieldCharDomain'
});

})();
