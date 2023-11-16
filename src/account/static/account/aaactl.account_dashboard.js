(function($, $tc, $ctl) {

$ctl.application.AaactlDashboard = $tc.extend(
  "AaactlDashboard",
  {
    AaactlDashboard : function() {
      const id = this.id = 'aaactl_dashboard';
      this.tools = this.$t = {}
      $(fullctl.application).trigger("initialized", [this, id]);
      $('[data-grainy-remove]').each(function() {
        $(this).grainy_toggle($(this).data("grainy-remove"), "r");
      });


      $('[data-bs-toggle="tab"]').on('show.bs.tab', function() {
        window.history.replaceState({}, document.title, $(this).attr("href"));
      });

      fullctl[id] = this;

      fullctl.auth.start_check();

      this.autoload_page();
    },
  },
  $ctl.application.Application
);

$(document).ready(function() {
  $ctl.aaactl_dashboard = new $ctl.application.AaactlDashboard();
});


})(jQuery, twentyc.cls, fullctl);
