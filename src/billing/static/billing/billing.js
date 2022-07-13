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
      $(this.rest_api_form).on("api-post:success", function() {
        if (this.rest_api_form.redirect){
          document.location.href = this.rest_api_form.redirect;
        } else {
          document.location.href = "/";
        }
      }.bind(this));
      this.elements.button_create_payopt.click(function() {
        this.toggle_create_payopt();
      }.bind(this));
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
    }
  }
);





})();
