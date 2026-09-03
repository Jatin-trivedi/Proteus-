/**
 * JOCKY Manager — Agent Fleet Overview & Orchestration API Binding
 */
(function () {
    'use strict';

    let isFetching = false;
    let pollInterval = null;

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function timeAgo(dateString) {
        if (!dateString) return 'never';
        const now = new Date();
        const date = new Date(dateString);
        const seconds = Math.floor((now - date) / 1000);
        if (seconds < 5) return 'just now';
        if (seconds < 60) return `${seconds}s ago`;
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    }

    function getOsIconSvg(osName) {
        const os = (osName || '').toLowerCase();
        if (os.includes('darwin') || os.includes('mac')) {
            return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20.94c1.88 0 3.05-.88 4.12-.88 1.07 0 2.09.88 4.12.88 2.52 0 4.76-2.02 4.76-5.18 0-3.32-2.19-5.12-4.35-5.12-1.74 0-2.83.99-3.79.99-.95 0-2.28-.99-3.86-.99-2.6 0-5 2.14-5 5.25 0 3.16 2.22 5.05 4 5.05z"/><path d="M15.5 6.5C16.8 5 17.5 3 17.5 1c-1.8.2-3.6 1.3-4.5 2.5-.9 1.2-1.5 3.1-1.5 5 2 0 3.3-1.1 4-2z"/></svg>`;
        }
        if (os.includes('win')) {
            return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>`;
        }
        return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>`;
    }

    /**
     * Fetch and render live Agent Fleet
     */
    async function loadFleetDashboard() {
        if (isFetching) return;
        isFetching = true;

        const btnRefresh = document.getElementById('btn-refresh');
        if (btnRefresh) {
            const svg = btnRefresh.querySelector('svg');
            if (svg) svg.classList.add('animate-spin');
            setTimeout(() => { if (svg) svg.classList.remove('animate-spin'); }, 600);
        }

        const elTotal = document.getElementById('metric-fleet-total');
        const elOnline = document.getElementById('metric-fleet-online');
        const elOffline = document.getElementById('metric-fleet-offline');
        const elUpdated = document.getElementById('fleet-last-updated');
        const container = document.getElementById('fleet-agent-list');

        try {
            const res = await fetch('/api/v1/agent/list');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const agents = await res.json();

            const total = agents.length;
            const online = agents.filter(a => a.status === 'online').length;
            const offline = total - online;

            if (elTotal) elTotal.textContent = total;
            if (elOnline) elOnline.textContent = online;
            if (elOffline) elOffline.textContent = offline;
            if (elUpdated) elUpdated.textContent = `Live · ${new Date().toLocaleTimeString()}`;

            if (!container) return;

            if (agents.length === 0) {
                const origin = window.location.origin || 'http://127.0.0.1:5001';
                container.innerHTML = `
                    <div class="p-6 text-center border border-dashed border-slate-300 dark:border-white/10 rounded-xl bg-slate-50/80 dark:bg-white/[0.02]">
                        <div class="w-12 h-12 rounded-xl bg-emerald/10 text-emerald flex items-center justify-center mx-auto mb-3">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2"></rect><line x1="8" x2="16" y1="21" y2="21"></line><line x1="12" x2="12" y1="17" y2="21"></line></svg>
                        </div>
                        <h4 class="font-heading text-base font-bold text-slate-900 dark:text-white mb-1">No Active Agents Registered</h4>
                        <p class="text-slate-500 dark:text-slate-400 text-xs max-w-sm mx-auto mb-3">Run the following command on your machine to connect an agent to this server:</p>
                        <div class="flex items-center justify-between gap-2 p-2.5 rounded-lg border border-slate-300 dark:border-white/10 bg-slate-100 dark:bg-slate-900 font-mono text-xs max-w-md mx-auto mb-4 text-left">
                            <code class="text-emerald truncate select-all">python local_agent.py --manager-url ${origin}</code>
                            <button onclick="copyConnectCommand(this)" class="shrink-0 px-2.5 py-1 rounded bg-emerald text-white text-[11px] font-sans font-semibold hover:bg-emerald-600 transition-all">Copy</button>
                        </div>
                        <a href="/scripts" class="soc-btn-primary inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold">Open Script Studio</a>
                    </div>
                `;
                return;
            }

            container.innerHTML = '';

            agents.forEach(agent => {
                const isOnline = agent.status === 'online';
                const arch = (agent.arch || 'ARM64').toUpperCase();
                const osName = (agent.os || 'UNKNOWN').toUpperCase();
                const osTag = `${osName} · ${arch}`;
                const timeAgoStr = timeAgo(agent.last_seen);
                const lastSeenTime = agent.last_seen ? new Date(agent.last_seen).toLocaleTimeString() : 'N/A';
                const osIcon = getOsIconSvg(agent.os);

                const card = document.createElement('div');
                card.className = `p-4 rounded-xl border transition-all duration-200 flex items-start gap-3.5 ${
                    isOnline 
                        ? 'border-emerald/20 dark:border-emerald/20 bg-slate-50/90 dark:bg-white/[0.03] hover:border-emerald/50' 
                        : 'border-slate-200 dark:border-white/8 bg-slate-50/50 dark:bg-white/[0.01]'
                }`;
                card.innerHTML = `
                    <!-- Left OS/Platform Icon Box -->
                    <div class="w-10 h-10 rounded-lg bg-emerald/10 border border-emerald/20 text-emerald flex items-center justify-center shrink-0 mt-0.5">
                        ${osIcon}
                    </div>

                    <!-- Main Card Body -->
                    <div class="flex-1 min-w-0">
                        <!-- Top Row: OS Tag + Online/Offline status badge -->
                        <div class="flex items-center justify-between gap-2 mb-1">
                            <span class="font-mono text-[11px] font-bold text-emerald uppercase tracking-wider truncate">${escapeHtml(osTag)}</span>
                            <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider ${
                                isOnline 
                                    ? 'bg-emerald/10 text-emerald border border-emerald/20' 
                                    : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                            }">
                                <span class="w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald animate-pulse-dot' : 'bg-slate-400'}"></span>
                                ${isOnline ? 'ONLINE' : 'OFFLINE'}
                            </span>
                        </div>

                        <!-- Middle Row: Hostname + ID & Description -->
                        <div class="mb-2">
                            <span class="font-heading font-bold text-slate-900 dark:text-white text-[15px]">${escapeHtml(agent.hostname || 'Unknown Host')}</span>
                            <span class="font-mono text-xs text-slate-400 dark:text-slate-500 ml-1">(${escapeHtml(agent.agent_id)})</span>
                            <p class="text-slate-500 dark:text-slate-400 text-xs mt-0.5">
                                Endpoint telemetry synchronized. Heartbeat reported <strong class="text-slate-700 dark:text-slate-200">${timeAgoStr}</strong>.
                            </p>
                        </div>

                        <!-- Bottom Meta Row: IP, Time, Deploy Payload, Delete -->
                        <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-200/80 dark:border-white/6 text-xs">
                            <div class="flex items-center gap-3 text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                                <span class="flex items-center gap-1.5">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                                    <code>${escapeHtml(agent.ip || '127.0.0.1')}</code>
                                </span>
                                <span class="flex items-center gap-1.5">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                    <span>${lastSeenTime}</span>
                                </span>
                            </div>
                            <div class="flex items-center gap-2">
                                <a href="/scripts?agent_id=${encodeURIComponent(agent.agent_id)}" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-slate-300 dark:border-white/10 bg-slate-100 dark:bg-white/5 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:border-slate-400 dark:hover:border-white/20 text-[11px] font-semibold transition-all">
                                    Deploy Payload
                                </a>
                                <button onclick="deleteFleetAgent('${escapeHtml(agent.agent_id)}', '${escapeHtml(agent.hostname || agent.agent_id)}')" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-rose-500/20 bg-rose-500/10 text-rose-500 dark:text-rose-400 hover:bg-rose-500/20 text-[11px] font-semibold transition-all cursor-pointer" title="Delete Agent">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        } catch (err) {
            console.error('[Dashboard API] Error:', err);
            if (container) {
                container.innerHTML = `
                    <div class="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-500 dark:text-rose-400 text-xs font-mono">
                        ⚠️ Unable to reach C2 Manager endpoint: ${escapeHtml(err.message)}
                    </div>
                `;
            }
        } finally {
            isFetching = false;
        }
    }

    window.deleteFleetAgent = async function (agentId, hostname) {
        if (!confirm(`Are you sure you want to delete agent "${hostname}" (${agentId})?\n\nThis will remove the agent and all its deployment history.`)) {
            return;
        }

        try {
            const res = await fetch('/api/v1/agent/' + encodeURIComponent(agentId), { method: 'DELETE' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            if (typeof showToast === 'function') {
                showToast(`Agent ${hostname || agentId} removed`, 'success');
            }
            loadFleetDashboard();
        } catch (err) {
            if (typeof showToast === 'function') {
                showToast('Failed to delete agent: ' + err.message, 'error');
            } else {
                alert('Failed to delete agent: ' + err.message);
            }
        }
    };

    window.copyConnectCommand = function (btn) {
        const origin = window.location.origin || 'http://127.0.0.1:5001';
        const cmd = `python local_agent.py --manager-url ${origin}`;
        
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(cmd).then(() => {
                if (typeof showToast === 'function') {
                    showToast('Connect command copied to clipboard!', 'success');
                } else {
                    alert('Copied to clipboard:\n' + cmd);
                }
            }).catch(() => fallbackCopy(cmd));
        } else {
            fallbackCopy(cmd);
        }

        function fallbackCopy(text) {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            if (typeof showToast === 'function') {
                showToast('Connect command copied to clipboard!', 'success');
            }
        }
    };

    window.loadFleetDashboard = loadFleetDashboard;

    // Boot
    function init() {
        loadFleetDashboard();
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(loadFleetDashboard, 6000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
