/* ─── THEME ────────────────────────────────────────────── */
(function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}

/* ─── TOAST NOTIFICATIONS ──────────────────────────────── */
window._showToast = function(message, type, duration) {
  type = type || 'info';
  duration = duration || 3500;
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const colors = {
    success: { bg: '#16a34a', icon: '✓' },
    error:   { bg: '#dc2626', icon: '✗' },
    warning: { bg: '#ea580c', icon: '⚠' },
    info:    { bg: '#3b82f6', icon: 'ℹ' },
  };
  const c = colors[type] || colors.info;
  const toast = document.createElement('div');
  toast.style.cssText = [
    'background:' + c.bg + ';color:#fff;padding:.65rem 1rem;',
    'border-radius:8px;font-size:.875rem;font-weight:500;',
    'box-shadow:0 4px 16px rgba(0,0,0,.25);',
    'display:flex;align-items:center;gap:.5rem;',
    'pointer-events:all;cursor:pointer;',
    'opacity:0;transform:translateY(8px);transition:all .22s ease-out;',
    'max-width:320px;word-break:break-word;'
  ].join('');
  var iconSpan = document.createElement('span');
  iconSpan.textContent = c.icon;
  var msgSpan = document.createElement('span');
  msgSpan.textContent = message;
  toast.appendChild(iconSpan);
  toast.appendChild(msgSpan);
  toast.onclick = function() { _dismissToast(toast); };
  container.appendChild(toast);
  requestAnimationFrame(function() {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  });
  setTimeout(function() { _dismissToast(toast); }, duration);
};

function _dismissToast(toast) {
  toast.style.opacity = '0';
  toast.style.transform = 'translateY(8px)';
  setTimeout(function() { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 240);
}

/* ─── COPY HELPER ──────────────────────────────────────── */
window._copyText = function(text, label) {
  navigator.clipboard.writeText(text).then(function() {
    window._showToast((label || 'Text') + ' copied to clipboard', 'success');
  }).catch(function() {
    window._showToast('Copy failed — select and copy manually', 'error');
  });
};

/* ─── KEYBOARD SHORTCUTS ───────────────────────────────── */
document.addEventListener('keydown', function(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
  if (e.altKey) {
    var shortcuts = { d: '/', e: '/events', i: '/itwins', g: '/integrations', w: '/webhooks', a: '/admin' };
    if (shortcuts[e.key]) { e.preventDefault(); window.location.href = shortcuts[e.key]; }
  }
  if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
    var searchEl = document.getElementById('searchInput') || document.getElementById('filterSearch');
    if (searchEl) { e.preventDefault(); searchEl.focus(); }
  }
});

/* ─── SIDEBAR ───────────────────────────────────────────── */
(function initSidebar() {
  var collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
  if (collapsed) document.body.classList.add('sidebar-collapsed');
})();

function toggleSidebar() {
  var isCollapsed = document.body.classList.toggle('sidebar-collapsed');
  localStorage.setItem('sidebarCollapsed', isCollapsed);
}

function openSidebar() {
  document.body.classList.add('sidebar-open');
}

function closeSidebar() {
  document.body.classList.remove('sidebar-open');
}

/* ─── FORMAT HELPERS ───────────────────────────────────── */
window._timeAgo = function(dateStr) {
  var secs = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (secs < 60) return secs + 's ago';
  if (secs < 3600) return Math.floor(secs / 60) + 'm ago';
  if (secs < 86400) return Math.floor(secs / 3600) + 'h ago';
  return Math.floor(secs / 86400) + 'd ago';
};

window._numFmt = function(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
};
