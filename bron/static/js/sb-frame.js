/* Q-Pall · SimplyBook-widget in een eigen frame (zelfde code als de officiële SimplyBook-snippet, in huisstijlkleuren). */
(function () {
  var q = new URLSearchParams(location.search);
  var loc = q.get('loc') || '4', cat = q.get('cat') || '8';
  /* hide SimplyBook's language picker + cart strip (see SB_CROP in site_config.py) */
  var crop = Math.max(0, parseInt(q.get('crop'), 10) || 0);
  document.documentElement.style.setProperty('--qp-crop', crop + 'px');
  if (typeof SimplybookWidget === 'undefined') {
    try { parent.postMessage({ qpSbError: 1 }, location.origin); } catch (e) {}
    return;
  }
  /* eslint-disable no-undef */
  var widget = new SimplybookWidget({
    "widget_type": "iframe",
    "url": "https://avkplasticsbv.simplybook.it",
    "theme": "default",
    "theme_settings": {
      "timeline_hide_unavailable": "1",
      "hide_past_days": "0",
      "timeline_show_end_time": "0",
      "timeline_modern_display": "as_slots",
      "sb_base_color": "#F37321",
      "display_item_mode": "block",
      "booking_nav_bg_color": "#1D1C4C",
      "body_bg_color": "#F8F8FA",
      "sb_review_image": "",
      "dark_font_color": "#1D1C4C",
      "light_font_color": "#ffffff",
      "btn_color_1": "#F37321",
      "sb_company_label_color": "#1D1C4C",
      "hide_img_mode": "0",
      "show_sidebar": "1",
      "sb_busy": "#E3E3EA",
      "sb_available": "#E2F3FB"
    },
    "timeline": "modern",
    "datepicker": "top_calendar",
    "is_rtl": false,
    "app_config": {
      "clear_session": 0,
      "allow_switch_to_ada": 0,
      "predefined": { "location": String(loc), "category": String(cat) }
    }
  });
  window.qpWidget = widget;
  /* tell the page when the booking frame has loaded, so it can remove its loading state */
  var ready = function () { setTimeout(function () { try { parent.postMessage({ qpSbReady: 1 }, location.origin); } catch (e) {} }, 250); };
  if (widget.frame) widget.frame.addEventListener('load', ready); else ready();
  function report() {
    var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
    try { parent.postMessage({ qpSbHeight: h }, location.origin); } catch (e) {}
  }
  if ('ResizeObserver' in window) { new ResizeObserver(report).observe(document.body); }
  setInterval(report, 1500);
  window.addEventListener('load', report);
})();
