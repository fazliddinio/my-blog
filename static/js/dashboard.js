/**
 * Dashboard interactions: sidebar toggle, alert auto-dismiss, slug auto-fill,
 * dynamic product-bullet rows. Vanilla JS, no dependencies.
 *
 * The mobile sidebar uses the same iOS-safe scroll-lock pattern as the
 * public site: store `scrollY`, pin the body with `position: fixed`, then
 * restore scroll when closing. See `static/css/style.css` -> `.body--no-scroll`.
 */
(function () {
  'use strict';

  // ---- Sidebar refs --------------------------------------------------------
  var sidebar = document.getElementById('dashSidebar');
  var toggle = document.getElementById('dashSidebarToggle');
  var overlay = document.getElementById('dashOverlay');

  // The sidebar collapses on tablets and below. Keep this in sync with the
  // matching CSS media query in `static/css/dashboard.css`.
  var MQ = window.matchMedia('(max-width: 1024px)');
  var BODY_LOCKED_CLASS = 'body--no-scroll';

  // Scroll-lock state. Local to this module so we don't accidentally double-
  // lock when other widgets request a lock at the same time.
  var lockedScrollY = 0;
  var locked = false;

  function isMobile() { return MQ.matches; }

  /** Pin the body in place at its current scroll position (iOS-safe). */
  function lockBody() {
    if (locked) return;
    lockedScrollY = window.scrollY || window.pageYOffset || 0;
    document.body.style.top = -lockedScrollY + 'px';
    document.body.classList.add(BODY_LOCKED_CLASS);
    locked = true;
  }

  /** Restore the body and scroll back to where the user was. */
  function unlockBody() {
    if (!locked) return;
    document.body.classList.remove(BODY_LOCKED_CLASS);
    document.body.style.top = '';
    window.scrollTo(0, lockedScrollY);
    locked = false;
  }

  function openSidebar() {
    if (!sidebar) return;
    if (sidebar.classList.contains('open')) return;
    sidebar.classList.add('open');
    if (overlay) overlay.classList.add('dash-overlay--visible');
    if (toggle) toggle.setAttribute('aria-expanded', 'true');
    if (isMobile()) lockBody();
  }

  function closeSidebar() {
    if (!sidebar) return;
    if (!sidebar.classList.contains('open')) {
      unlockBody();
      return;
    }
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('dash-overlay--visible');
    if (toggle) toggle.setAttribute('aria-expanded', 'false');
    unlockBody();
  }

  if (toggle && sidebar) {
    toggle.addEventListener('click', function () {
      if (sidebar.classList.contains('open')) closeSidebar();
      else openSidebar();
    });
  }

  if (overlay) overlay.addEventListener('click', closeSidebar);

  // Close sidebar when tapping a nav link on mobile (so the next page renders without the menu open).
  if (sidebar) {
    sidebar.querySelectorAll('a, button[type="submit"]').forEach(function (el) {
      el.addEventListener('click', function () { if (isMobile()) closeSidebar(); });
    });
  }

  // Escape closes the sidebar.
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) closeSidebar();
  });

  // Reset state when crossing the breakpoint (e.g. user rotates a tablet).
  MQ.addEventListener && MQ.addEventListener('change', function () { closeSidebar(); });

  // Auto-dismiss alerts.
  document.querySelectorAll('.dash-alert').forEach(function (el) {
    setTimeout(function () {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-8px)';
      setTimeout(function () { el.remove(); }, 300);
    }, 4000);
  });

  // Confirm delete actions.
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('submit', function (e) {
      if (!confirm(el.getAttribute('data-confirm') || 'Are you sure?')) e.preventDefault();
    });
  });

  // Auto-generate slug from title.
  var titleInput = document.getElementById('id_title_en') || document.getElementById('id_name_en');
  var slugInput = document.getElementById('id_slug');
  if (titleInput && slugInput && !slugInput.value) {
    titleInput.addEventListener('input', function () {
      slugInput.value = titleInput.value
        .toLowerCase().replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-').replace(/-+/g, '-').trim();
    });
  }

  // Add bullet point row.
  var addBulletBtn = document.getElementById('addBullet');
  if (addBulletBtn) {
    addBulletBtn.addEventListener('click', function () {
      var container = document.getElementById('bulletsList');
      if (!container) return;
      var row = document.createElement('div');
      row.className = 'dash-form__row';
      row.innerHTML =
        '<div class="dash-form__group" style="flex:1;">' +
        '<input type="text" name="bullet_text_en" class="dash-form__input" placeholder="Bullet (English)">' +
        '</div>' +
        '<div class="dash-form__group" style="flex:1;">' +
        '<input type="text" name="bullet_text_uz" class="dash-form__input" placeholder="Bullet (Uzbek)">' +
        '</div>' +
        '<button type="button" class="btn btn--ghost btn--sm" data-remove-row style="align-self:flex-end;margin-bottom:4px;">Remove</button>';
      container.appendChild(row);
    });
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-remove-row]');
    if (btn && btn.parentElement) btn.parentElement.remove();
  });
})();
