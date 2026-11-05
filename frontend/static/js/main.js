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

// Confirm destructive form submissions (e.g. deleting a post)
(function () {
  "use strict";
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.getAttribute("data-confirm"))) event.preventDefault();
    });
  });

  // Filter dropdown (<details>): close on outside click or Escape
  document.querySelectorAll("details[data-filter-menu]").forEach(function (menu) {
    document.addEventListener("click", function (event) {
      if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && menu.open) {
        menu.open = false;
        menu.querySelector("summary").focus();
      }
    });
  });

  // Post form: highlight a row when its event is checked, and focus its time input
  document.querySelectorAll("[data-event-toggle]").forEach(function (box) {
    var row = box.closest(".event-row");
    var time = row && row.querySelector(".event-row__time input");
    box.addEventListener("change", function () {
      row.classList.toggle("is-checked", box.checked);
      if (box.checked && time && !time.value) time.focus();
    });
    if (time) {
      time.addEventListener("input", function () {
        if (time.value && !box.checked) { box.checked = true; row.classList.add("is-checked"); }
      });
    }
  });
})();
