(function () {
  'use strict';

  // Sidebar toggle for mobile
  var toggle = document.getElementById('dashSidebarToggle');
  var sidebar = document.getElementById('dashSidebar');
  var overlay = document.getElementById('dashOverlay');

  if (toggle && sidebar) {
    toggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      if (overlay) overlay.classList.toggle('dash-overlay--visible');
    });
  }

  if (overlay) {
    overlay.addEventListener('click', function () {
      sidebar.classList.remove('open');
      overlay.classList.remove('dash-overlay--visible');
    });
  }

  // Auto-dismiss alerts after 4s
  document.querySelectorAll('.dash-alert').forEach(function (el) {
    setTimeout(function () {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-8px)';
      setTimeout(function () { el.remove(); }, 300);
    }, 4000);
  });

  // Confirm delete actions
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('submit', function (e) {
      if (!confirm(el.getAttribute('data-confirm') || 'Are you sure?')) {
        e.preventDefault();
      }
    });
  });

  // Auto-generate slug from title
  var titleInput = document.getElementById('id_title_en') || document.getElementById('id_name_en');
  var slugInput = document.getElementById('id_slug');
  if (titleInput && slugInput && !slugInput.value) {
    titleInput.addEventListener('input', function () {
      slugInput.value = titleInput.value
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim();
    });
  }

  // Add bullet point row
  var addBulletBtn = document.getElementById('addBullet');
  if (addBulletBtn) {
    addBulletBtn.addEventListener('click', function () {
      var container = document.getElementById('bulletsList');
      var row = document.createElement('div');
      row.className = 'dash-form__row';
      row.innerHTML =
        '<div class="dash-form__group" style="flex:1;">' +
        '<input type="text" name="bullet_text_en" class="dash-form__input" placeholder="Bullet (English)">' +
        '</div>' +
        '<div class="dash-form__group" style="flex:1;">' +
        '<input type="text" name="bullet_text_uz" class="dash-form__input" placeholder="Bullet (Uzbek)">' +
        '</div>' +
        '<button type="button" class="btn btn--ghost btn--sm" onclick="this.parentElement.remove()" style="align-self:flex-end;margin-bottom:4px;">Remove</button>';
      container.appendChild(row);
    });
  }
})();
