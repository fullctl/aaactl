(function() {

window.account = {}

account.api_client = new twentyc.rest.Client("/api/account")

account.ControlPanel = twentyc.cls.define(
  "ControlPanel",
  {
    ControlPanel : function() {
      this.elements = {};
      this.forms = {};

      this.loadDropDown()
      this.styleDropDown();

      this.createOrganization();
      this.editOrganization();

      this.changePassword();
      
      this.elements.order_history = $('.order-history');
      this.order_history_list = new twentyc.rest.List(this.elements.order_history);
      this.buildOrderHistory();

      this.elements.resend_confirmation_email = $('form.resend-confirmation-email');
      if(this.elements.resend_confirmation_email.length  > 0)
        this.resend_confirmation_email = new twentyc.rest.Form(this.elements.resend_confirmation_email);
      $(this.resend_confirmation_email).on("api-post:success", function() {
        alert("Email has been sent");
      });

      $(this.resend_confirmation_email).on("api-post:error", function(event, endpoint, data, response) {
        console.log(response.content);
      }.bind(this));

    },

    buildOrderHistory: function() {
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
            .attr('href', '/billing/order-history/details/' + value)
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
        $('.org-select-menu').children().last().wrap('<div class="custom-divider"></div')
        $('.org-select-menu').append(`<a class="dropdown-item org-item" role="button" data-toggle="modal" data-target="#createOrgModal">+ Create Organization</a>`)
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
          alert("User password updated!")
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

account.EditOrganization = twentyc.cls.define(
  "EditOrganization",
  {
    EditOrganization : function() {
      this.elements = {}
      this.elements.form = $('form.edit-organization');

      this.rest_api_form = new twentyc.rest.Form(this.elements.form);
      $(this.rest_api_form).on("api-write:success", function() {
        alert("Organization updated");
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
          editor.find('[data-field="component"]').text(component);
          widget = new twentyc.rest.PermissionsForm(editor);
          widget.fill(data);
          widget.fill({component:component});
          widget.set_flag_values(value[component]);
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


account.PasswordReset = twentyc.cls.define(
  "PasswordReset",
  {
    PasswordReset : function() {
      this.elements = {}
      this.elements.form = $('form.password-reset');

      this.rest_api_form = new twentyc.rest.Form(this.elements.form);
      $(this.rest_api_form).on("api-post:success", function() {
          if(this.rest_api_form.base_url.match(/\/start$/)) {
            alert("Password reset instructions have been sent to you, provided the email address was found in our system.")

          } else {
            document.location.href = "/";
          }
      }.bind(this));
    }
  }
);

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
        )
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
        return $('<td>').append([
          $('<span>').text('Usage: ').addClass('light-grey table-text-thin'),
          $('<span>').text(this.editedUsageType()).addClass('dark-grey table-text-large')
        ])
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
        return $('<td>').append([
          $('<span>').text('Usage: ').addClass('light-grey table-text-thin'),
          $('<span>').text(this.editedUsageAmount()).addClass('dark-grey table-text-large')
        ])
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
        return $('<td>').text('$' + Number(this.cost).toFixed(2)).addClass('dark-grey table-text-large text-align-right')
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
