(function($, $tc) {
window.fullctl = {
  urlparam : new URLSearchParams(window.location.search)
}

var fullctl = window.fullctl;

fullctl.help_box = document.addEventListener("DOMContentLoaded", () => {
  const help_button = document.querySelector(".help-btn");
  const box = document.querySelector(".help-box");

  help_button.addEventListener('click', () => {
    box.classList.toggle("js-hide");
    box.style.bottom = help_button.getBoundingClientRect().bottom - help_button.getBoundingClientRect().top + "px";

    document.addEventListener("click", (event) => {
      if (event.target.closest(".help-box")) return;
      if (event.target.closest(".help-btn")) return;
      box.classList.add("js-hide");
    })
  })
});

fullctl.theme_switching = document.addEventListener("DOMContentLoaded", () => {
  function get_system_theme() {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  matchMedia('(prefers-color-scheme: dark)').onchange = (e) => {
    let system_theme = get_system_theme();
    // Update the theme, as long as there's no theme override
    if (localStorage.getItem('theme') === null) {
      set_theme(system_theme);
    }
  }

  function toggle_theme() {
      if (detect_theme() === 'dark')
          set_theme('light');
      else
          set_theme('dark');
  }

  function set_theme(newTheme) {
    document.documentElement.setAttribute('data-theme', newTheme)
    if (newTheme === get_system_theme()) {
      // Remove override if the user sets the theme to match the system theme
      localStorage.removeItem('theme')
    } else {
      localStorage.setItem('theme', newTheme)
    }
  }

  function detect_theme() {
      var theme_override = localStorage.getItem('theme')
      if (theme_override == 'dark' || theme_override === 'light') {
          // Override the system theme
          return theme_override
      }
      // Use system theme
      return get_system_theme();
  }

  document.documentElement.setAttribute('data-theme', detect_theme())

  $(".theme-switcher").click(() => {
      toggle_theme();
  });
});

})(jQuery, twentyc.cls);

