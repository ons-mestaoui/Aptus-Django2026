/* ============================================================
   APTUS AI — Theme Toggle
   Manages Light/Dark mode with localStorage persistence
   ============================================================ */

(function() {
  'use strict';

  const STORAGE_KEY = 'aptus-theme';
  const html = document.documentElement;

  function getPreferredTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function setTheme(theme, isManual = false) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    updateToggleIcons(theme);
    
    // Save to DB via AJAX if user is logged in AND it's a manual toggle
    if (isManual && window.APTUS_BASE_URL) {
      const formData = new FormData();
      formData.append('action', 'update_preferences');
      formData.append('theme', theme);
      
      fetch(window.APTUS_BASE_URL + 'view/frontoffice/ajax_handler.php', {
        method: 'POST',
        body: formData
      }).catch(err => console.warn("Theme sync failed:", err));
    }
  }

  function updateToggleIcons(theme) {
    document.querySelectorAll('.theme-toggle').forEach(function(btn) {
      var sunIcon = btn.querySelector('.icon-sun');
      var moonIcon = btn.querySelector('.icon-moon');
      if (sunIcon && moonIcon) {
        if (theme === 'dark') {
          sunIcon.style.display = 'block';
          moonIcon.style.display = 'none';
        } else {
          sunIcon.style.display = 'none';
          moonIcon.style.display = 'block';
        }
      }
    });
  }

  function toggleTheme() {
    var current = html.getAttribute('data-theme') || 'light';
    setTheme(current === 'dark' ? 'light' : 'dark', true);
  }

  // Initialize on load (if not already set by layout_front.php)
  const currentTheme = html.getAttribute('data-theme');
  const preferredTheme = getPreferredTheme();
  if (currentTheme !== preferredTheme) {
    setTheme(preferredTheme);
  } else {
    updateToggleIcons(preferredTheme);
  }

  // Listen for system preference changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
    if (!localStorage.getItem(STORAGE_KEY)) {
      setTheme(e.matches ? 'dark' : 'light');
    }
  });

  // Expose toggle function globally
  window.AptusTheme = {
    toggle: toggleTheme,
    set: setTheme,
    get: function() { return html.getAttribute('data-theme') || 'light'; }
  };

  // Auto-bind toggle buttons
  document.addEventListener('DOMContentLoaded', function() {
    updateToggleIcons(getPreferredTheme());
    document.querySelectorAll('.theme-toggle').forEach(function(btn) {
      btn.addEventListener('click', toggleTheme);
    });
  });
})();
