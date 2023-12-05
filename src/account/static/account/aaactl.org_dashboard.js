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
