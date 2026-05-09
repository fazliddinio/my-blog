// ============================================================
// fazliddin.com — Client-side JavaScript
// i18n, mobile nav, AJAX forms, code copy, scroll header
// ============================================================

(function () {
  'use strict';

  // -------- Language (i18n) --------
  const LANG_KEY = 'fz_lang';

  function getLang() {
    return getCookie(LANG_KEY) || 'en';
  }

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
  }

  function getCSRFToken() {
    var cookie = getCookie('csrftoken');
    if (cookie) return cookie;
    var input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  }

  window.setLang = function (lang) {
    document.cookie = LANG_KEY + '=' + lang + ';path=/;max-age=31536000;SameSite=Lax';
    applyLang(lang);
    updateLangToggles(lang);
  };

  function applyLang(lang) {
    document.querySelectorAll('.tr').forEach(function (el) {
      const en = el.getAttribute('data-en');
      const uz = el.getAttribute('data-uz');
      if (lang === 'uz' && uz) {
        el.innerHTML = uz;
      } else if (en) {
        el.innerHTML = en;
      }
    });
    document.documentElement.lang = lang;
  }

  function updateLangToggles(lang) {
    document.querySelectorAll('.lang-toggle button').forEach(function (btn) {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
    });
  }

  // -------- Header scroll effect --------
  function initHeaderScroll() {
    var header = document.getElementById('siteHeader');
    if (!header) return;
    function onScroll() {
      header.classList.toggle('scrolled', window.scrollY > 4);
    }
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // -------- Mobile nav --------
  function initMobileNav() {
    var btn = document.getElementById('mobileMenuBtn');
    var nav = document.getElementById('mobileNav');
    if (!btn || !nav) return;

    btn.addEventListener('click', function () {
      var isOpen = nav.style.display !== 'none';
      nav.style.display = isOpen ? 'none' : 'grid';
      btn.setAttribute('aria-expanded', !isOpen);
      var header = document.getElementById('siteHeader');
      if (header) header.classList.toggle('scrolled', !isOpen || window.scrollY > 4);
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 820) {
        nav.style.display = 'none';
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // -------- AJAX form submission --------
  function initAjaxForms() {
    // Newsletter forms
    document.querySelectorAll('#newsletterForm, [data-newsletter-form]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var formData = new FormData(form);
        var btn = form.querySelector('button[type="submit"]');
        var originalText = btn.innerHTML;

        fetch(form.action, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken(),
          },
          body: formData,
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.ok) {
              var lang = getLang();
              btn.innerHTML = lang === 'uz' ? "Obuna bo'ldingiz ✓" : 'Subscribed ✓';
              btn.disabled = true;
              showToast(data.message);
              form.querySelector('input[type="email"]').value = '';
              setTimeout(function () {
                btn.innerHTML = originalText;
                btn.disabled = false;
              }, 3000);
            } else {
              showToast('Please enter a valid email.');
            }
          })
          .catch(function () {
            showToast('Something went wrong. Try again.');
          });
      });
    });

    // Contact form
    var contactForm = document.getElementById('contactForm');
    if (contactForm) {
      contactForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var formData = new FormData(contactForm);
        var btn = contactForm.querySelector('button[type="submit"]');
        var originalText = btn.innerHTML;

        fetch(contactForm.action, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken(),
          },
          body: formData,
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.ok) {
              var lang = getLang();
              btn.innerHTML = lang === 'uz' ? 'Yuborildi ✓' : 'Sent ✓';
              btn.disabled = true;
              showToast(data.message);
              contactForm.reset();
              setTimeout(function () {
                btn.innerHTML = originalText;
                btn.disabled = false;
              }, 3000);
            } else {
              showToast('Please fill in all fields.');
            }
          })
          .catch(function () {
            showToast('Something went wrong. Try again.');
          });
      });
    }
  }

  // -------- Code block copy --------
  function initCodeCopy() {
    document.querySelectorAll('.code-block__copy').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var pre = btn.closest('.code-block').querySelector('pre');
        if (!pre) return;
        navigator.clipboard.writeText(pre.textContent).then(function () {
          btn.textContent = 'Copied';
          btn.classList.add('copied');
          setTimeout(function () {
            btn.textContent = 'Copy';
            btn.classList.remove('copied');
          }, 1400);
        });
      });
    });
  }

  // -------- Toast --------
  window.showToast = function showToast(message) {
    var toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(function () {
      toast.classList.remove('show');
    }, 2800);
  }

  // -------- Init --------
  document.addEventListener('DOMContentLoaded', function () {
    applyLang(getLang());
    initHeaderScroll();
    initMobileNav();
    initAjaxForms();
    initCodeCopy();
  });
})();
