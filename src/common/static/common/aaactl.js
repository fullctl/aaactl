(function() {

window.aaactl = {}

aaactl.api_client = new twentyc.rest.Client("/api/account")

aaactl.Header = twentyc.cls.define(
  "Header",
  {
    Header : function() {
      this.elements = {}
      this.elements.app_switcher = $('[data-element="app_switcher"]');

      const others = this.elements.app_switcher.find('.others')
      const selected = this.elements.app_switcher.find('.selected')
      selected.click(() => {
        others.show();
        selected.addClass('app_bg muted');
      });
      $(document.body).click(function(e) {
        if (
          !( $(e.target).is(selected) || $(e.target).parent().hasClass('selected') )
        ) {
          others.hide();
          selected.removeClass('app_bg muted');
        }
      });

      this.app_switcher = new twentyc.rest.List(this.elements.app_switcher);

      this.app_switcher.formatters.row = (row, data) => {
        const redirect_url = data.service_url.replace("{org.slug}", account.org.slug)
        const img =  row.find("img.app-logo")

        row.attr("href", redirect_url);
        if(!data.logo) {
          img.attr("src", img.data("logo-url").replace("svc_slug", data.slug));
        } else {
          img.attr("src", data.logo);
        }
      };

      this.app_switcher.load();
    },
  }
);

})(jQuery, twentyc.cls);