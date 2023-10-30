(function($, $tc, $ctl) {

billing.BillingContactAddress = $tc.extend(
  "DeviceWidget",
  {
    DeviceWidget: function (jq) {
      this.Form(jq);

      const billing_contact_id = this.element.find('[name="id"]').val();
      const billing_contact_api_url = twentyc.rest.url.url_join(
        this.base_url,
        this.action
      );

      const form = this;
      $.ajax({
        type: "GET",
        url: billing_contact_api_url,
        dataType: 'json',
        data: $.param({"id": billing_contact_id}),
        success: function(data, status){
          if (data.data[0]) {
            form.fill(data.data[0].address)
          }
        }
      });
    },

    payload : function() {
      const payload = this.Form_payload();
      payload.address = {
        holder: payload.name,
        country: payload.country,
        address1: payload.address1,
        address2: payload.address2,
        city: payload.city,
        state: payload.state,
        postal_code: payload.postal_code,
      }

      delete payload.country;
      delete payload.address1;
      delete payload.address2;
      delete payload.city;
      delete payload.state;
      delete payload.postal_code;

      return payload;
    }
  },
  twentyc.rest.Form
);

$(document).ready(() => {
  new billing.BillingContactAddress($('[data-element="billing_contact_address"]'));
});

})(jQuery, twentyc.cls, fullctl);