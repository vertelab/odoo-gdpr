$(document).ready(function() {
});

$(".confirm_consent").live('change', function() {
    var $self = $(this);
    openerp.jsonRpc("/mail/consent/confirm", 'call', {
        'inventory_id': $self.data("inventory_id"),
        'consent_id': $self.data("consent_id"),
        'partner_id': $self.data("partner_id"),
        'confirm': $self.is(':checked')
    }).done(function(data) {
        if(data == 'ok') {
            var $tr = $self.closest("tr");
            $("#consent_table").load(document.URL + " #consent_table");
        }
    });
});
