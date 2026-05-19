/**
 * fazliddin.com — client-side enhancements.
 *
 * Goals of this file:
 *   1. Keep the page usable and accessible without JS as much as possible.
 *      Everything here progressively enhances HTML/CSS that already works.
 *   2. Avoid framework dependencies — vanilla JS, IIFE-wrapped, ~10 KB gzipped.
 *   3. Never rely on layout side-effects of opening a panel; we pin scroll
 *      explicitly with `lockBodyScroll` so iOS Safari behaves correctly.
 *
 * The dark/light theme is applied synchronously in `<head>` to prevent a
 * flash of incorrect theme; this file only handles the toggle button.
 */

(function () {
  'use strict';

  var LANG_KEY = 'fz_lang';
  var THEME_KEY = 'fz_theme';

  // ---------------------------------------------------------------- helpers
  function getCookie(name) {
    var match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
  }

  function setCookie(name, value, days) {
    var maxAge = (days || 365) * 86400;
    document.cookie = name + '=' + encodeURIComponent(value) +
      ';path=/;max-age=' + maxAge + ';SameSite=Lax';
  }

  function getCSRFToken() {
    return getCookie('csrftoken') || (function () {
      var input = document.querySelector('[name=csrfmiddlewaretoken]');
      return input ? input.value : '';
    })();
  }

  // ---------------------------------------------------------------- toast
  var toastTimer = null;
  window.showToast = function (message, opts) {
    var toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.toggle('toast--error', !!(opts && opts.error));
    toast.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('show'); }, 2800);
  };

  // ---------------------------------------------------------------- language
  // Server-rendered text is the source of truth. Switching language reloads
  // the page after writing the cookie.
  function initLanguageToggles() {
    document.querySelectorAll('.lang-toggle button[data-lang]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var lang = btn.getAttribute('data-lang') || 'en';
        var current = getCookie(LANG_KEY) || 'en';
        if (lang === current) return;
        setCookie(LANG_KEY, lang);
        window.location.reload();
      });
    });
  }

  // ---------------------------------------------------------------- theme
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
  }

  function initThemeToggle() {
    function toggle() {
      var current = document.documentElement.getAttribute('data-theme') || 'light';
      var next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
    }
    var btn = document.getElementById('themeToggle');
    if (btn) btn.addEventListener('click', toggle);
  }

  // ---------------------------------------------------------------- header
  function initHeaderScroll() {
    var header = document.getElementById('siteHeader');
    if (!header) return;

    function syncHeaderHeight() {
      var inner = header.querySelector('.header-inner');
      var height = inner ? inner.getBoundingClientRect().height : header.getBoundingClientRect().height;
      header.style.setProperty('--header-height', Math.ceil(height) + 'px');
    }

    function onScroll() { header.classList.toggle('scrolled', window.scrollY > 4); }

    syncHeaderHeight();
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', syncHeaderHeight);
    window.addEventListener('orientationchange', syncHeaderHeight);
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', syncHeaderHeight);
    }
  }

  // ---------------------------------------------------------------- body scroll lock (iOS-safe)
  // Stores the current scrollY when locking, restores it when unlocking.
  // Multiple panels (nav, sidebar) can request a lock; we refcount them.
  var lockCount = 0;
  var lockedScrollY = 0;
  var BODY_LOCKED = 'body--no-scroll';

  window.lockBodyScroll = function () {
    if (lockCount === 0) {
      lockedScrollY = window.scrollY || window.pageYOffset || 0;
      document.body.style.top = -lockedScrollY + 'px';
      document.body.classList.add(BODY_LOCKED);
    }
    lockCount += 1;
  };

  window.unlockBodyScroll = function () {
    lockCount = Math.max(0, lockCount - 1);
    if (lockCount === 0) {
      document.body.classList.remove(BODY_LOCKED);
      document.body.style.top = '';
      // Restore the scroll position the user had before locking.
      window.scrollTo(0, lockedScrollY);
    }
  };

  // ---------------------------------------------------------------- mobile nav
  function initMobileNav() {
    var header = document.getElementById('siteHeader');
    var btn = document.getElementById('mobileMenuBtn');
    var nav = document.getElementById('mobileNav');
    var overlay = document.getElementById('mobileNavOverlay');
    if (!btn || !nav) return;

    var MQ = window.matchMedia('(max-width: 820px)');
    var suppressOutsideCloseUntil = 0;

    function isMobile() { return MQ.matches; }

    function setOpenState(open) {
      nav.hidden = !open;
      if (overlay) {
        overlay.hidden = !open;
        overlay.setAttribute('aria-hidden', open ? 'false' : 'true');
      }
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (header) header.classList.toggle('mobile-nav-open', open);
    }

    function close() {
      if (nav.hidden) return;
      setOpenState(false);
      window.unlockBodyScroll();
    }

    function open() {
      if (!nav.hidden) return;
      setOpenState(true);
      window.lockBodyScroll();
      // iOS Safari can emit a ghost click on the overlay right after opening.
      suppressOutsideCloseUntil = Date.now() + 350;
    }

    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (nav.hidden) open(); else close();
    });

    if (overlay) {
      overlay.addEventListener('click', function () {
        if (Date.now() < suppressOutsideCloseUntil) return;
        close();
      });
    }

    // Close when a link is tapped — the next page should render with a clean header.
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) close();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !nav.hidden) {
        close();
        btn.focus();
      }
    });

    function handleBreakpointChange() {
      if (!isMobile()) close();
    }

    if (MQ.addEventListener) MQ.addEventListener('change', handleBreakpointChange);
    else if (MQ.addListener) MQ.addListener(handleBreakpointChange);

    window.addEventListener('resize', handleBreakpointChange);
  }

  // ---------------------------------------------------------------- AJAX forms
  function bindAjaxForm(form, opts) {
    if (!form) return;
    var btn = form.querySelector('button[type="submit"]');
    var original = btn ? btn.innerHTML : '';

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (btn) {
        btn.disabled = true;
        btn.classList.add('is-loading');
        btn.innerHTML = (opts.loading || 'Sending') + '…';
      }

      fetch(form.action, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCSRFToken(),
          'Accept': 'application/json',
        },
        body: new FormData(form),
      })
        .then(function (r) {
          return r.json().then(function (data) { return { status: r.status, data: data }; });
        })
        .then(function (out) {
          var ok = out.data && out.data.ok;
          var msg = (out.data && out.data.message) || (ok ? 'Done' : 'Something went wrong.');
          showToast(msg, { error: !ok });
          if (ok) {
            if (btn) {
              btn.classList.remove('is-loading');
              btn.classList.add('is-success');
              btn.innerHTML = (opts.success || 'Done') + ' ✓';
            }
            form.reset();
            setTimeout(function () {
              if (btn) {
                btn.disabled = false;
                btn.classList.remove('is-success');
                btn.innerHTML = original;
              }
            }, 3500);
          } else {
            if (btn) {
              btn.disabled = false;
              btn.classList.remove('is-loading');
              btn.innerHTML = original;
            }
          }
        })
        .catch(function () {
          showToast('Network error — please try again.', { error: true });
          if (btn) {
            btn.disabled = false;
            btn.classList.remove('is-loading');
            btn.innerHTML = original;
          }
        });
    });
  }

  function initAjaxForms() {
    document.querySelectorAll('#newsletterForm, [data-newsletter-form]').forEach(function (f) {
      bindAjaxForm(f, { loading: 'Subscribing', success: 'Subscribed' });
    });
    bindAjaxForm(document.getElementById('contactForm'), { loading: 'Sending', success: 'Sent' });
  }

  // ---------------------------------------------------------------- code copy
  function initCodeCopy() {
    document.querySelectorAll('.code-block__copy').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var pre = btn.closest('.code-block') && btn.closest('.code-block').querySelector('pre');
        if (!pre || !navigator.clipboard) return;
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

  // ---------------------------------------------------------------- reading progress
  function initReadingProgress() {
    var bar = document.getElementById('readingProgress');
    var article = document.querySelector('[data-reading-progress]');
    if (!bar || !article) return;
    function onScroll() {
      var rect = article.getBoundingClientRect();
      var total = article.offsetHeight - window.innerHeight;
      if (total <= 0) { bar.style.width = '0%'; return; }
      var scrolled = Math.min(Math.max(-rect.top, 0), total);
      bar.style.width = (scrolled / total * 100) + '%';
    }
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // ---------------------------------------------------------------- toast triggers
  function initToastTriggers() {
    document.addEventListener('click', function (e) {
      var el = e.target.closest('[data-toast]');
      if (!el) return;
      e.preventDefault();
      showToast(el.getAttribute('data-toast') || 'Done');
    });
  }

  // ---------------------------------------------------------------- focus contact input
  function initContactScroll() {
    document.querySelectorAll('a[href="#contact"]').forEach(function (a) {
      a.addEventListener('click', function () {
        setTimeout(function () {
          var first = document.querySelector('#contactForm input, #contactForm textarea');
          if (first) first.focus({ preventScroll: false });
        }, 250);
      });
    });
  }

  // ---------------------------------------------------------------- init
  document.addEventListener('DOMContentLoaded', function () {
    initLanguageToggles();
    initThemeToggle();
    initHeaderScroll();
    initMobileNav();
    initAjaxForms();
    initCodeCopy();
    initReadingProgress();
    initToastTriggers();
    initContactScroll();
  });
})();
