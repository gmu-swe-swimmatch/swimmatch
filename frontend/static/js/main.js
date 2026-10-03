// SwimMatch — small progressive enhancements. Everything works without JS.
(function () {
  "use strict";

  // Mobile nav toggle
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("primary-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Dismissible flash messages
  document.querySelectorAll(".flash__close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      btn.closest(".flash").remove();
    });
  });

  // Auto-submit filter selects on change
  document.querySelectorAll("form[data-autosubmit] select").forEach(function (select) {
    select.addEventListener("change", function () {
      select.form.submit();
    });
  });
})();
