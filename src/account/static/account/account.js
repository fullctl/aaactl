(function() {

window.account = {}

account.api_client = new twentyc.rest.Client("/api/account")

account.ControlPanel = twentyc.cls.define(
  "ControlPanel",
  {
    ControlPanel : function() {
      this.elements = {};
      this.forms = {};

      this.loadDropDown();
      this.styleDropDown();

      this.createOrganization();
      this.editOrganization();

      this.changePassword();

      this.elements.order_history = $('.order_history-history');
      if(this.elements.order_history.length > 0) {
        this.order_history_list = new twentyc.rest.List(this.elements.order_history);
      }
      this.buildOrderHistory();

      this.elements.resend_confirmation_email = $('form.resend-confirmation-email');
      if(this.elements.resend_confirmation_email.length  > 0)
        this.resend_confirmation_email = new twentyc.rest.Form(this.elements.resend_confirmation_email);
      $(this.resend_confirmation_email).on("api-post:success", function() {
        this.popoverAlert(
          this.resend_confirmation_email.element.find('button.submit'),
          "Confirmation email has been sent"
        );

      }.bind(this));

      $(this.resend_confirmation_email).on("api-post:error", function(event, endpoint, data, response) {
        console.log(response.content);
      }.bind(this));

      this.personal_invites = new account.PersonalInvites();

    },

    postFromLink: function(url) {
      $.ajax({
        method: "post",
        url: url,
        headers : {
          "X-CSRFToken": twentyc.rest.config.csrf
        }
      }).done(() => { window.document.location.href = window.document.location.href })
    },

    buildOrderHistory: function() {

      // if the user isn't provisioned to view the order_history history this
      // property wont be set and we can just return
      if(!this.order_history_list)
        return;

      this.order_history_list.formatters.description = function(value, data) {
        return $('<span>').append(
          $('<strong>').text(value),
        );
      }
      this.order_history_list.formatters.processed = function(value, data) {
        var date = new Date(value)
        return $('<span>').append(
          $('<span>').text(date.toDateString().split(' ').slice(1).join(' ')),
        );
      }
      this.order_history_list.formatters.price = function(value, data) {
        return $('<span>').append(
          $('<strong>').text('USD $' + value),
        );
      }
      this.order_history_list.formatters.order_id = function(value, data) {
        return $('<span>').append(
          $('<a>')
            .attr('href', '/billing/order_history-history/details/' + value)
            .text('Details')
        );
      }
      $(this.order_history_list).on("load:after", () => {
        if ( $("#orderHistoryListBody:empty").length ){
          $('#orderHistoryListBody')
            .append('<tr><td>No entries</td></tr>')
        }
      })
      this.order_history_list.load();
    },

    loadDropDown: function(){
      this.dropDown = new twentyc.rest.List($('.org-select'));
      $('.org-select-dropdown-header').empty();


      this.dropDown.formatters.label = (value, data) => {
        if(data.is_default) {
          return value + " (Primary)";
        }
        return value;
      }


      $(this.dropDown).on("insert:after", (e, row, data) => {
        row.attr('href', '/?org='+ data.slug)
        if (data.selected) {
          $('.org-select-dropdown-header')
            .append($('<span>').text(data.label).addClass('float-left'))
            .append($('<span>').addClass('caret down float-right'));
          row.hide();
        };
      });
      $(this.dropDown).on("load:after", ()=> {
        var menu = $('.org-select-menu');

        menu.children().last().wrap('<div class="custom-divider"></div');

        var btn_make_default = new twentyc.rest.Button(this.dropDown.template("btn_make_default"));
        $(btn_make_default).on('api-write:success', ()=>{ this.loadDropDown(); });
        menu.append(btn_make_default.element)

        menu.append(`<a class="dropdown-item org-item" role="button" data-toggle="modal" data-target="#createOrgModal">+ Create Organization</a>`)
      });
      this.dropDown.load();
    },

    styleDropDown: function() {
      $(".dropdown").on("hide.bs.dropdown", function(){
        $(".org-select").removeClass('dd-box-shadow');
        $(".caret").removeClass('up').addClass('down');
      });
      $(".dropdown").on("show.bs.dropdown", function(){
        $(".org-select").addClass('dd-box-shadow');
        $(".caret").removeClass('down').addClass('up');
      });
    },

    createOrganization: function(){
      this.initializeForm('create-organization', '/');
      this.forms['create_organization'].post_success = function(response){
        var slug = response.content.data[0].slug;
        document.location.href = `/?org=${slug}`
      }
    },

    editOrganization: function(){
      this.initializeForm('edit-organization');
      $(this.forms['edit_organization']).on("api-write:success", function() {
        document.location.href = '/';
      });
    },

    changePassword: function(){
      this.initializeForm('change-password');
      var has_usuable_password = !$('#setPasswordAlert').length;

      if ( has_usuable_password ){
        $(this.forms['change_password']).on("api-write:success", function() {
          $('#collapseFour').collapse('hide');
          $('#changePwdPopover').popover('show');
          $('.change-password input').val("");
          setTimeout(() => {
              $('#changePwdPopover').popover('hide');
          }, 4000);

        })
      } else {
        $(this.forms['change_password']).on("api-write:success", function() {
          document.location.href = "/";
        })
      }


    },

    initializeForm: function(form_class){
      var form_name = form_class.replace('-','_');
      this.elements[form_name] = $(`form.${form_class}`);
      this.forms[form_name] = new twentyc.rest.Form(this.elements[form_name]);
    },

    popoverAlert : function(anchor, text) {
      anchor.popover({
        trigger: 'manual',
        content: text
      })
      anchor.popover('show');
      setTimeout(() => {
        anchor.popover('hide');
        anchor.popover('dispose');
      }, 2000);
    }
});



account.ChangeInformation = twentyc.cls.define(
  "ChangeInformation",
  {
    ChangeInformation : function() {
      this.elements = {}
      this.elements.form = $('form.change-information');

      this.styleAccountInformation();

      this.rest_api_form = new twentyc.rest.Form(this.elements.form);
      $(this.rest_api_form).on("api-write:success", function() {
        document.location.href = "/"
      }.bind(this));
    },

    styleAccountInformation : function() {
      $('.collapse').on('show.bs.collapse', function () {
        $( this ).parent().css('background-color','rgba(224, 225, 226, 0.6)');
      });
      $('.collapse').on('hidden.bs.collapse', function () {
        $( this ).parent().css('background-color','rgba(224, 225, 226, 0)');
      });
    },
  }
);


account.UserSettings = twentyc.cls.define(
  "UserSettings",
  {
    UserSettings : function() {
      this.elements = {}
      this.elements.form = $('form.user-settings');

      this.styleAccountInformation();

      this.rest_api_form = new twentyc.rest.Form(this.elements.form);
      $(this.rest_api_form).on("api-write:success", function() {
        document.location.href = "/"
      }.bind(this));
    },

    styleAccountInformation : function() {
      $('.collapse').on('show.bs.collapse', function () {
        $( this ).parent().css('background-color','rgba(224, 225, 226, 0.6)');
      });
      $('.collapse').on('hidden.bs.collapse', function () {
        $( this ).parent().css('background-color','rgba(224, 225, 226, 0)');
      });
    },
  }
);



account.ChangePassword = twentyc.cls.define(
  "ChangePassword",
  {
    ChangePassword : function() {
      this.elements = {}
      this.elements.form = $('form.change-password');

      this.rest_api_form = new twentyc.rest.Form(this.elements.form);
      $(this.rest_api_form).on("api-write:success", function() {
        if(this.rest_api_form.redirect) {
          document.location.href = this.rest_api_form.redirect;
        } else {
          document.location.href = "/"
        }
      }.bind(this));
    }
  }
);


account.CreateOrganization = twentyc.cls.define(
  "CreateOrganization",
  {
    CreateOrganization : function() {
      this.elements = {}
      this.elements.form = $('form.create-organization');

      this.rest_api_form = new twentyc.rest.Form(this.elements.form);
      $(this.rest_api_form).on("api-write:success", function() {
        if(this.rest_api_form.redirect) {
          document.location.href = this.rest_api_form.redirect;
        }
      }.bind(this));
    }
  }
);

account.UsersList = twentyc.cls.define(
  "UsersList",
  {
    UsersList : function() {
      this.elements = {}
      this.elements.user_listing = $('.user-listing')

      this.rest_api_list = new twentyc.rest.List(this.elements.user_listing);

      this.rest_api_list.formatters.permissions = function(value, data) {
        if(!data.manageable.match(/ud/))
          return;
        var component, editor, widget, container = $('<div>');
        for(component in value) {
          editor = this.template("permissions")
          var label = value[component].label
          widget = new twentyc.rest.PermissionsForm(editor);
          widget.fill(data);
          widget.fill({component:component});
          widget.set_flag_values(value[component]);
          editor.find('[data-field="component"]').text(label);
          container.append(editor)
        }
        return container;
      }.bind(this.rest_api_list)

      this.rest_api_list.formatters.row = function(row,data) {
        var manage_container = row.filter('.manage')
        if(data.you) {
          row.find('.btn.manage').attr('disabled', true);
          row.find('.btn.manage')
            .text('You')
            .removeClass('btn-manage')
            .addClass('btn-disabled')
        }
        else if(!data.manageable.match(/[ud]/)) {
          row.find('.btn.manage').hide();
        }
        else {
          row.find('.btn.manage').click(function() {
            if(manage_container.is(':visible'))
              manage_container.hide();
            else
              manage_container.show();
          });
        }
        manage_container.hide();
      }

      this.rest_api_list.load();
    }
  }
);

account.OrgKeysList = twentyc.cls.define(
  "OrgKeysList",
  {
    OrgKeysList : function() {
      this.elements = {}
      this.elements.orgkey_listing = $('.org_key-listing')

      this.rest_api_list = new twentyc.rest.List(this.elements.orgkey_listing);

      this.rest_api_list.formatters.permissions = function(value, data) {
        if(!data.manageable.match(/ud/))
          return;
        var component, editor, widget, container = $('<div>');
        for(component in value) {
          editor = this.template("permissions")
          var label = value[component].label
          widget = new twentyc.rest.PermissionsForm(editor);
          widget.fill(data);
          widget.fill({component:component});
          widget.set_flag_values(value[component]);
          editor.find('[data-field="component"]').text(label);
          container.append(editor)
        }
        return container;
      }.bind(this.rest_api_list)

      this.rest_api_list.formatters.row = function(row,data) {
        var manage_container = row.filter('.manage')
        if(data.you) {
          row.find('.btn.manage').attr('disabled', true);
          row.find('.btn.manage')
            .text('You')
            .removeClass('btn-manage')
            .addClass('btn-disabled')
        }
        else if(!data.manageable.match(/[ud]/)) {
          row.find('.btn.manage').hide();
        }
        else {
          row.find('.btn.manage').click(function() {
            if(manage_container.is(':visible'))
              manage_container.hide();
            else
              manage_container.show();
          });
        }
        manage_container.hide();
      }

      $(this.rest_api_list).on("insert:after", (e, row, data) => {
        this.enableShowButton(row, data);
        this.enableCopyButton(row);
      })

      // Modal
      this.elements.orgkey_form = $('form.create_orgkey');
      if ( this.elements.orgkey_form.length ){
        this.rest_orgkey_form = new twentyc.rest.Form(this.elements.orgkey_form);
        $(this.rest_orgkey_form).on("api-write:success", function() {
          $('#orgApiKeyModal').modal('toggle');
          this.rest_api_list.load();
        }.bind(this));
      }


      this.rest_api_list.load();
    },
    enableShowButton: function(row, data) {
      var key = data.key;
      var redacted_key = key.replace(key.slice(2,-2), '*'.repeat(key.length-4));
      var keybox_redacted = row.find('.org-key-box-redacted');
      var keybox_display = row.find('.org-key-box');
      var show_button = row.find('.show-button');

      keybox_redacted.val(redacted_key);
      keybox_display.val(key);

      show_button.click(() => {
        keybox_redacted.toggleClass('d-none');
        keybox_display.toggleClass('d-none');
      })
    },
    enableCopyButton: function(row) {
      var copy_button = row.find('.copy-button');
      var keybox_redacted = row.find('.org-key-box-redacted');
      var keybox_display = row.find('.org-key-box');
      copy_button.click(() => {
          if ( keybox_display.hasClass('d-none') ){
            keybox_redacted.addClass('d-none');
            keybox_display.removeClass('d-none');
            keybox_display.select();
            document.execCommand("copy");
            keybox_redacted.removeClass('d-none');
            keybox_display.addClass('d-none');
            keybox_redacted.select();
          } else {
            keybox_display.select();
            document.execCommand("copy");
          }
      })
    }

  }

);



account.PasswordReset = twentyc.cls.define(
  "PasswordReset",
  {
    PasswordReset : function() {
      this.elements = {}
      this.elements.form = $('form.password-reset');

      this.rest_api_form = new twentyc.rest.Form(this.elements.form);
      $(this.rest_api_form).on("api-post:success", function() {
          if(this.rest_api_form.base_url.match(/\/start$/)) {
            this.rest_api_form.element.hide()
            this.rest_api_form.element.siblings('.alert-success').show()
            this.rest_api_form.element.siblings('.alert-info').hide()
          } else {
            document.location.href = "/";
          }
      }.bind(this));
    }
  }
);

account.ServiceApplications = twentyc.cls.define(
  "ServiceApplications",
  {
    ServiceApplications : function() {
      this.element = $('.service-apps-listing');
      this.rest_api_list = new twentyc.rest.List(this.element);

      this.rest_api_list.formatters.row = (row, data) => {
        let redirect_url = data.invite_redirect.replace("{org.slug}", account.org.slug)
        let img= row.find("img.logo")
        row.find("a.redirect").attr("href", redirect_url);
        if(!data.logo) {
          img.attr("src", img.data("logo-url").replace("svc_slug", data.slug));
        } else {
          img.attr("src", data.logo);
        }
      };

      this.rest_api_list.load();


    }
});


account.Services = twentyc.cls.define(
  "Services",
  {
    Services : function() {
      this.element = $('.service-listing');
      this.rest_api_list = new twentyc.rest.List(this.element);

      $(this.rest_api_list).on("insert:after", (e, row, data) => {
        var item_heading = row;
        item_heading.addClass('item-group clearfix');
        var total_cost = 0;

        var item_table = $('<table>').addClass('item-table');
        item_heading.after(item_table);
        data.items.forEach((item, idx, array) => {
          var ihf = new this.itemHtmlFormatter(item);
          item_table.append(
              $('<tr>').append([
                ihf.formattedDescription(),
                ihf.formattedUsageType(),
                ihf.formattedUsageAmount(),,
                ihf.formattedLink().hide(),
                ihf.formattedCost()
              ])
            )
          total_cost += parseFloat(item.cost);
        });
        item_heading.children().append(
          $('<span>').addClass('float-right').append([
             $('<span>').text('Total Monthly Cost: ').addClass('lighter-grey'),
             $('<span>').text('$' + Number(total_cost).toFixed(2)).addClass('table-text-bold white')
          ])
        );
        item_table.children().first().children().addClass('pt-2');
        item_table.children().last().children().addClass('pb-2');
        item_table.after($('<tr>').addClass('blank-row'));
      });

      $(this.rest_api_list).on("load:after", () => {
        if ( $("#serviceListBody:empty").length ){
          $('#serviceListBody')
            .append('<tr><td class="pt-0 pb-3 px-0">No service subscriptions</td></tr>')
        }
      })

      this.rest_api_list.load();
    },
    itemHtmlFormatter: function(item) {
      this.description = item.description;
      this.type = item.type;
      this.usage = item.usage;
      this.cost = item.cost;
      this.unit_name_plural = item.unit_name_plural;
      this.unit_name = item.unit_name;

      this.formattedDescription = () => {
        return $('<td>').text(this.description).addClass('dark-grey table-text-bold')
      }
      this.formattedUsageType = () => {
        if(this.type == "Fixed Price") {
          return $('<td>');
        } else {
          return $('<td>').append([
            $('<span>').text('Usage: ').addClass('light-grey table-text-thin'),
            $('<span>').text(this.editedUsageType()).addClass('dark-grey table-text-large')
          ])
        }
      }
      this.editedUsageType = () => {
        if ( this.type == 'Metered Usage') {
          return 'metered'
        }
        else {
          return this.type.toLowerCase()
        }
      }

      this.formattedUsageAmount = () => {
        if(this.type == "Fixed Price") {
          return $('<td>');
        } else {
          return $('<td>').append([
            $('<span>').text('Usage: ').addClass('light-grey table-text-thin'),
            $('<span>').text(this.editedUsageAmount()).addClass('dark-grey table-text-large')
          ])
        }
      }

      this.editedUsageAmount = () => {
        if ( this.usage === 1 ){
          return this.usage + ' ' + this.unit_name
        } else {
          return this.usage + ' ' + this.unit_name_plural
        }
      }

      this.formattedLink = () => {
        return $('<td>').addClass('small-links').append(
          $('<a>').attr('href','/').text('Details')
        )
      }

      this.formattedCost = () => {
        return $('<td>').text('$' + Number(this.cost).toFixed(2)).addClass('dark-grey table-text-large text-align-right right')
      }
    }
});


account.PersonalAPIKeys = twentyc.cls.define(
  "PersonalAPIKeys",
  {
    PersonalAPIKeys: function() {
      this.element = $('.personal-keys');
      this.rest_api_list = new twentyc.rest.List(this.element);

      this.rest_api_list.formatters.created = function(value, data){
        var d = new Date(value);
        return d.toDateString().split(' ').slice(1).join(' ')
      }


      $(this.rest_api_list).on("insert:after", (e, row, data) => {
        this.enableShowButton(row, data);
        this.enableCopyButton(row);
      })

      this.rest_api_list.formatters.readonly = function(value) {

        if(value)
          return "read-only"
        return ""
      };

      // Modal
      var key_form = $('form.create_key');
      if ( key_form.length ){
        this.rest_key_form = new twentyc.rest.Form(key_form);
        $(this.rest_key_form).on("api-write:success", function() {
          $('#personalApiKeyModal').modal('toggle');
          this.rest_api_list.load();
        }.bind(this));
      }


      this.rest_api_list.load();
    },
    enableShowButton: function(row, data) {
      var key = data.key;
      var redacted_key = key.replace(key.slice(2,-2), '*'.repeat(key.length-4));
      var keybox_redacted = row.find('.personal-key-box-redacted');
      var keybox_display = row.find('.personal-key-box');
      var show_button = row.find('.show-button');

      keybox_redacted.val(redacted_key);
      keybox_display.val(key);

      show_button.click(() => {
        keybox_redacted.toggleClass('d-none');
        keybox_display.toggleClass('d-none');
      })
    },
    enableCopyButton: function(row) {
      var copy_button = row.find('.copy-button');
      var keybox_redacted = row.find('.personal-key-box-redacted');
      var keybox_display = row.find('.personal-key-box');
      copy_button.click(() => {
          if ( keybox_display.hasClass('d-none') ){
            keybox_redacted.addClass('d-none');
            keybox_display.removeClass('d-none');
            keybox_display.select();
            document.execCommand("copy");
            keybox_redacted.removeClass('d-none');
            keybox_display.addClass('d-none');
            keybox_redacted.select();
          } else {
            keybox_display.select();
            document.execCommand("copy");
          }
      })
    }
})

account.PersonalInvites = twentyc.cls.define(
  "PersonalInvites",
  {
    PersonalInvites: function() {
      this.element = $('.personal-invites');
      this.rest_api_list = new twentyc.rest.List(this.element);

      $(this.rest_api_list).on("api-get:success", (ev, e, d, response) => {
        if(response.content.data.length > 0)
          $('#count-invites').text("("+response.content.data.length+")");
      });

      this.rest_api_list.formatters.row = (row, data) => {
        var button_accept = new twentyc.rest.Button(row.find('button.accept-invite'));
        var button_reject = new twentyc.rest.Button(row.find('button.reject-invite'));

        button_accept.format_request_url = (url) => {
          return url.replace(/invite_id/g, data.id);
        }

        button_reject.format_request_url = (url) => {
          return url.replace(/invite_id/g, data.id);
        }

        $(button_reject).on("api-write:success", () => {
          this.rest_api_list.load();
        });

        $(button_accept).on("api-write:success", () => {
          this.rest_api_list.load();
          window.controlpanel.loadDropDown();
          window.controlpanel.styleDropDown();
        });

      };

      this.rest_api_list.load();
    }
  }
)



account.PendingUsers = twentyc.cls.define(
  "PendingUsers",
  {
    PendingUsers: function() {
      this.elements = {}
      this.elements.pending_user_listing = $('.pending-user-listing');
      this.rest_api_list = new twentyc.rest.List(this.elements.pending_user_listing);


      this.rest_api_list.formatters.created = function(value, data){
        var d = new Date(value);
        return d.toDateString().split(' ').slice(1).join(' ')
      }

      this.rest_api_list.formatters.user_name = function(value, data){
        if ( value === '' ) {
          return value + '<span class="user-badge ub-pending">Pending</span>';
        } else {
          return value + '<span class="user-badge ub-pending ml-2">Pending</span>';
        }
      }

      $(this.rest_api_list).on("insert:after", (e, row, data) => {
        var client = new twentyc.rest.Client("/api/account");
        if ( row.find('.name-column').text() === 'Pending' ) {
          row.find('.name-column').addClass('text-center');
        }

        var payload = {
          email: data.email,
          service: "",
        }
        var a = row.find('.resend-invite');
        if ( a.length ){
          var endpoint = `org/${data.slug}/invite`;
          a.click(() => client.post(endpoint, payload));
          $(client).on('api-write:success', () => {
            // Initialize popover
            a.popover({
              trigger: 'manual',
              content: `Invite re-sent to ${data.email}`
            })
            a.popover('show');
            setTimeout(() => {
              a.popover('hide');
              a.popover('dispose');
            }, 2000);
          })
          $(client).on('api-write:error', (event, endpoint, data, response) => {
            // Initialize popover
            var error_message = response.http_status_text();
            a.popover({
              trigger: 'manual',
              html: true,
              content: `<p style="color:red;">${error_message}</p>`,
            })
            a.popover('show');
            setTimeout(() => {
              a.popover('hide');
              a.popover('dispose');
            }, 6000);

          });
        }
      })

      // Modal
      this.elements.invitation_form = $('form.invite');
      if ( this.elements.invitation_form.length ){
        this.rest_invite_form = new twentyc.rest.Form(this.elements.invitation_form);
        $(this.rest_invite_form).on("api-write:success", function() {
          $('#inviteModal').modal('toggle');
          this.rest_api_list.load();
        }.bind(this));
      }

      this.rest_api_list.load();
    }
})
})();
