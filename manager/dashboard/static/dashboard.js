/**
 * JOCKY Manager — Dashboard Frontend Utilities & Theme Management
 */

function initTheme() {
  const savedTheme = localStorage.getItem('jocky-theme') || 'dark';
  setTheme(savedTheme);
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  if (theme === 'light') {
    document.documentElement.classList.add('light');
  } else {
    document.documentElement.classList.remove('light');
  }
  localStorage.setItem('jocky-theme', theme);
  updateThemeIcon(theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const target = current === 'dark' ? 'light' : 'dark';
  setTheme(target);
  showToast(`Switched to ${target === 'dark' ? 'Dark' : 'Light'} Mode`, 'info');
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('theme-toggle-btn');
  if (!btn) return;
  if (theme === 'dark') {
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>`;
    btn.setAttribute('title', 'Switch to Light Mode');
  } else {
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`;
    btn.setAttribute('title', 'Switch to Dark Mode');
  }
}

function timeAgo(dateString) {
  if (!dateString) return 'Never';
  const now = new Date();
  const date = new Date(dateString);
  const seconds = Math.floor((now - date) / 1000);
  if (seconds < 5)  return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24)   return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function copyToClipboard(text, btnElement) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      if (btnElement) {
        const original = btnElement.innerHTML;
        btnElement.innerHTML = '✓ Copied';
        setTimeout(() => { btnElement.innerHTML = original; }, 2000);
      }
    });
  }
}

function getOsIcon(osName) {
  const os = (osName || '').toLowerCase();
  if (os.includes('win')) {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="8" height="8"/><rect x="13" y="3" width="8" height="8"/><rect x="3" y="13" width="8" height="8"/><rect x="13" y="13" width="8" height="8"/></svg>`;
  } else if (os.includes('darwin') || os.includes('mac')) {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 5c-2.22 0-4 1.44-5 2-1-.56-2.78-2-5-2a4.9 4.9 0 0 0-5 4.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06Z"/><path d="M10 2c1 .5 2 2 2 5"/></svg>`;
  } else if (os.includes('linux')) {
    return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m10 15 5-3-5-3v6Z"/></svg>`;
  }
  return `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" x2="16" y1="21" y2="21"/><line x1="12" x2="12" y1="17" y2="21"/></svg>`;
}

function showToast(message, type = 'info') {
  let container = document.getElementById('jocky-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'jocky-toast-container';
    container.className = 'fixed bottom-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none';
    document.body.appendChild(container);
  }

  const colorMap = {
    success: { bar: '#10b981', icon: '✓', text: 'text-emerald-400' },
    error:   { bar: '#f43f5e', icon: '✕', text: 'text-rose-400'    },
    info:    { bar: '#06b6d4', icon: 'ℹ', text: 'text-cyan-400'    },
  };
  const c = colorMap[type] || colorMap.info;

  const toast = document.createElement('div');
  toast.className = 'pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl border border-white/10 shadow-2xl font-body text-sm text-slate-200';
  toast.style.cssText = `background: rgba(10,10,18,0.95); backdrop-filter: blur(16px); border-left: 3px solid ${c.bar};`;
  toast.innerHTML = `<span class="${c.text} font-bold text-base leading-none">${c.icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  // Animate in via global helper if available
  if (window.animateToastIn) window.animateToastIn(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 360);
  }, 3500);
}

document.addEventListener('DOMContentLoaded', initTheme);