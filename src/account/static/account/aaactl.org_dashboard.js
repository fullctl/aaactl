(function($, $tc, $ctl) {

$ctl.application.AaactlDashboard = $tc.extend(
  "AaactlDashboard",
  {
    AaactlDashboard : function() {
      const id = this.id = 'aaactl_dashboard';
      this.tools = this.$t = {};
      $(fullctl.application).trigger("initialized", [this, id]);
      $('[data-grainy-remove]').each(function() {
        $(this).grainy_toggle($(this).data("grainy-remove"), "r");
      });


      $('[data-bs-toggle="tab"]').on('show.bs.tab', function() {
        window.history.replaceState({}, document.title, $(this).attr("href"));
      });

      fullctl[id] = this;

      fullctl.auth.start_check();

      this.tool("org_dashboard", () => {
        return new $ctl.application.OrgDashboard();
      });

      this.autoload_page();
    },
  },
  $ctl.application.Application
);

$ctl.application.OrgDashboard = $tc.extend(
  "OrgDashboard",
  {
    OrgDashboard : function() {
      this.Tool("org_dashboard");

      this.widget("org_api_keys", () => {
        return new $ctl.application.OrgKeysList();
      });

      this.widget("leave_org_button", () => {
        return new $ctl.application.LeaveOrgButton(this.$e.leave_org_button)
      });
      $(this.$w.leave_org_button).on("api-delete:success", () => {
        location.reload();
      })

      if (this.$e.delete_org_button) {
        this.set_up_delete_org_button();
      }
    },

    set_up_delete_org_button : function() {
      this.$e.delete_org_button.on("click", () => {
        new $ctl.application.Modal(
          "no_button",
          "Delete Organization?",
          this.$t.delete_org_modal_body
        );
      });
    },

    menu : function() {}
  },
  $ctl.application.Tool
);

/**
 * List of API Keys for an organization with controls to manage perms
 * for each key
 *
 * @class OrgKeysList
 * @constructor
 */

$ctl.application.OrgKeysList = twentyc.cls.define(
  "OrgKeysList",
  {
    OrgKeysList : function() {
      this.elements = {}
      this.elements.org_key_listing = $('.org_key-listing')

      this.rest_api_list = new twentyc.rest.List(this.elements.org_key_listing);

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

        row.find('[data-action="edit"]').on("click", function() {
          new $ctl.application.ModalEditOrgAPIKeyDetails(data);
        });

        if(data.you) {
          row.find('.manage').attr('disabled', true);
          row.find('.manage')
            .text('You')
            .removeClass('btn-manage')
            .addClass('btn-disabled')
        }
        else if(!data.manageable.match(/[ud]/)) {
          row.find('.manage').hide();
        }
        else {
          row.find('.manage').click(function() {
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
      this.elements.org_key_form = $('form.create_org_key');
      if ( this.elements.org_key_form.length ){
        this.rest_org_key_form = new twentyc.rest.Form(this.elements.org_key_form);
        $(this.rest_org_key_form).on("api-write:success", function() {
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
    },

    sync : function() {
      this.rest_api_list.load();
    }
  }
);

/**
 * Modal that can be used to edit API Key details
 *
 * @class ModalEditOrgAPIKeyDetails
 * @extends fullctl.application.Modal
 * @constructor
 * @param {Object} data OrganizationAPIKey api object which is being edited.
 */

$ctl.application.ModalEditOrgAPIKeyDetails = $tc.extend(
  "ModalEditOrgAPIKeyDetails",
  {
    ModalEditOrgAPIKeyDetails : function(data) {
      const modal = this;
      const title = "Edit API Key Details";
      const form = this.form = new twentyc.rest.Form(
        $ctl.template("form_org_api_key_details")
      );

      $(this.form).on("api-write:success", (ev, e, payload, response) => {
        modal.hide();
        $ctl.aaactl_dashboard.tools.org_dashboard.$w.org_api_keys.sync();
      });

      form.fill(data)

      this.Modal("save", title, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);



$ctl.application.LeaveOrgButton = $tc.extend(
  "LeaveOrgButton",
  {
    LeaveOrgModal : function(jq) {
      this.Button(jq);
    },

    render_non_field_errors : function(errors) {
      // render error of only admin as a modal
      if (errors.includes("Cannot remove yourself as you are the only admin for the org.")) {
        new $ctl.application.Modal(
          "no_button",
          "Error!",
          $ctl.aaactl_dashboard.tools.org_dashboard.$t.error_only_admin_message
        );
      } else {
        this.Button_render_non_field_errors(errors);
      }
    }
  },
  twentyc.rest.Button
);

$(document).ready(function() {
  $ctl.aaactl_dashboard = new $ctl.application.AaactlDashboard();
});


})(jQuery, twentyc.cls, fullctl);
