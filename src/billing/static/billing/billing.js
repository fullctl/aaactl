(function() {

window.billing = {}

billing.api_client = new twentyc.rest.Client("/api/billing");

billing.BillingContact = twentyc.cls.define(
  "BillingContact",
  {
    BillingContact : function() {
      this.elements = {}
      this.elements.payment_method_list = $('.payment_method-listing')
      this.elements.billing_contact_form = $('form.billing_contact')

      this.rest_api_payment_method_list = new twentyc.rest.List(this.elements.payment_method_list);
      this.rest_api_payment_method_list.format_request_url = (url) => {
        let billing_contact_id = this.elements.payment_method_list.data('billing-contact-id');
        return `${url}?billing_contact=${billing_contact_id}`
      }
      this.rest_api_payment_method_list.formatters.updated = fullctl.formatters.datetime;
      this.rest_api_payment_method_list.load()

      this.rest_api_billing_contact_form = new twentyc.rest.Form(this.elements.billing_contact_form);
      $(this.rest_api_billing_contact_form).on('api-delete:success', function() {
        document.location.href = "/billing/billing-contacts/";
      });
    }
  }
);

billing.BillingSetup = twentyc.cls.define(
  "BillingSetup",
  {
    BillingSetup : function() {
      this.elements = {}
      this.elements.form = $('form.billing-setup');
      this.elements.section_create_payopt = this.elements.form.find('#form-create-payopt');
      this.elements.section_select_payopt = this.elements.form.find('#form-select-payopt');
      this.elements.button_create_payopt = this.elements.form.find('.toggle-create-payopt');
      this.elements.select_payopt = this.elements.form.find('[name="payment_method"]')

      this.initial_payopt = this.elements.select_payopt.val()

      this.rest_api_form = new twentyc.rest.Form(this.elements.form);
      this.fill_address();
      this.track_form_changes();
      $(this.rest_api_form).on("api-post:success", function(e, endpoint, sent_data, response) {
        console.log("Got submit success", {e, endpoint, response, sent_data});
        window.processorHandleConfirm(response.first().payment_method_id);
      }.bind(this));
      this.elements.button_create_payopt.click(function() {
        this.toggle_create_payopt();
      }.bind(this));


      this.elements.return_to_dashbaord = $('a.return-to-dashbaord');
      this.elements.return_to_dashbaord.on('click', (e) => {
        if (this.elements.form.attr('data-submitted') == 'true') {
          this.elements.form.attr('data-submitted', 'false');
        } else if (this.changed) {
          const conrimation = confirm("Are you sure you want to close this modal? Any unsaved changes will be lost.");
          if (!conrimation) {
            e.preventDefault();
            return;
          }
        }
      })
    },

    track_form_changes : function() {
      const billing_contact_form = this.rest_api_form;
      this.changed = false;

      billing_contact_form.element.find('input').on('change', () => {
        this.changed = true;
      });
      $(billing_contact_form).on('api-post:success api-delete:success', function() {
        billing_contact_form.element.attr('data-submitted', 'true');
      })
    },

    toggle_create_payopt : function() {
      if(this.elements.section_create_payopt.is(":visible"))
        this.hide_create_payopt();
      else
        this.show_create_payopt();
    },

    show_create_payopt : function() {
      this.elements.select_payopt.val(0);
      this.elements.section_create_payopt.collapse("show");
      this.elements.section_select_payopt.collapse("hide");
    },

    hide_create_payopt : function() {
      this.elements.select_payopt.val(this.inital_payopt);
      this.elements.section_create_payopt.collapse("hide");
      this.elements.section_select_payopt.collapse("show");
    },

    fill_address : function() {
      const urlParams = new URLSearchParams(document.location.search);
      const billing_contact_id = urlParams.get('billing_contact');
      const billing_contact_api_url = twentyc.rest.url.url_join(
        this.rest_api_form.base_url,
        this.rest_api_form.element.data('api-action-autofill')
      );

      const form = this.rest_api_form.element;
      $.ajax({
        type: "GET",
        url: billing_contact_api_url,
        dataType: 'json',
        data: $.param({"id": billing_contact_id}),
        success: function(data, status){
          if (!data.data[0]) {
            return;
          }

          const address = data.data[0].address;
          if (!address) {
            return
          }

          if (address.country) {
            form.find('[name="country"]').val(address.country);
          }
          if (address.city) {
            form.find('[name="city"]').val(address.city);
          }
          if (address.state) {
            form.find('[name="state"]').val(address.state);
          }
          if (address.postal_code) {
            form.find('[name="postal_code"]').val(address.postal_code);
          }
          if (address.address1) {
            form.find('[name="address1"]').val(address.address1);
          }
          if (address.address2) {
            form.find('[name="address2"]').val(address.address2);
          }

        }
      });
    }
  }
);


})();
