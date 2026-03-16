(function() {
    const API_URL = window.API_URL || window.location.origin;
    let token = localStorage.getItem('token');
    window.token = token;
    let currentUser = {}; 
    window.currentUser = currentUser;

// ============================================
// 1. AUTH CHECK & REDIRECT
// ============================================
if (!token) {
    window.location.href = '/';
}

    // Unified Sidebar Loading
    async function loadSidebar() {
        const sidebarContainer = document.getElementById('sidebar-container');
        if (!sidebarContainer) return;
        
        try {
            const res = await fetch('/static/components/sidebar.html');
            if (res.ok) {
                sidebarContainer.innerHTML = await res.text();
                initSidebarEvents();
                if (window.lucide) lucide.createIcons();
            }
        } catch (err) {
            console.error('Sidebar load failed:', err);
        }
    }

    function initSidebarEvents() {
        const logoutBtn = document.getElementById('logout-btn') || document.getElementById('logout-btn-sidebar');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                localStorage.removeItem('token');
                window.location.href = '/';
            });
        }

        const settingsBtn = document.getElementById('open-settings-btn') || document.getElementById('open-settings-btn-sidebar');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                openSettingsView();
            });
        }

        // Sidebar Navigation Links
        const navLinks = {
            'uptime-link': 'uptime-view',
            'incidents-link': 'incidents-view',
            'reports-link': 'reports-view', // Note: reports often has its own page
            'status-pages-link': 'status-pages-view',
            'infrastructure-link': 'infrastructure-view',
            'notifications-link': 'notifications-view'
        };

        Object.keys(navLinks).forEach(id => {
            const link = document.getElementById(id);
            if (link) {
                link.addEventListener('click', (e) => {
                    const viewId = navLinks[id];
                    // If we are on dashboard.html, we showView, else we might need to redirect
                    if (document.getElementById(viewId)) {
                        e.preventDefault();
                        showView(viewId);
                    }
                });
            }
        });
    }

    // Call sidebar load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadSidebar);
    } else {
        loadSidebar();
    }

// ============================================
// 2. THEME TOGGLE FUNCTIONALITY
// ============================================
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}
window.toggleTheme = toggleTheme; // Expose globally

// Initialize theme from localStorage
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') {
    document.documentElement.classList.remove('dark');
} else {
    document.documentElement.classList.add('dark');
}

// Attach theme toggle button event listener
const themeToggleBtn = document.getElementById('theme-toggle');
if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', toggleTheme);
}

// ============================================
// 3. MODAL CONTROLS
// ============================================
function toggleModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.toggle('hidden');
        modal.classList.toggle('flex');
    }
}
window.toggleModal = toggleModal; // Expose globally

// ============================================
// 4. SETTINGS VIEW
// ============================================
function openSettingsView() {
    // Populate settings fields
    if (currentUser && Object.keys(currentUser).length > 0) {
        const nameEl = document.getElementById('setting-name');
        const emailEl = document.getElementById('setting-email');
        const roleEl = document.getElementById('setting-role');
        
        if (nameEl) nameEl.innerText = currentUser.name || 'N/A';
        if (emailEl) emailEl.innerText = currentUser.email || 'N/A';
        if (roleEl) roleEl.innerText = currentUser.role === 'admin' ? 'Super Admin' : 'Team Member';
        
        // Show/hide admin panel
        const adminPanel = document.getElementById('admin-view-panel');
        if (adminPanel) {
            if (currentUser.role === 'admin') {
                adminPanel.classList.remove('hidden');
            } else {
                adminPanel.classList.add('hidden');
            }
        }
    }
    
    // Show settings view, hide others
    showView('settings-view');
}
window.openSettingsView = openSettingsView; // Expose globally

// Attach settings button event listener (moved to initSidebarEvents)

// ============================================
// 5. SIDEBAR NAVIGATION
// ============================================
function showView(viewId) {
    // Hide all views
    const views = ['uptime-view', 'infrastructure-view', 'notifications-view', 'incidents-view', 'status-pages-view', 'settings-view'];
    views.forEach(id => {
        const view = document.getElementById(id);
        if (view) view.classList.add('hidden');
    });
    
    // Show selected view
    const selectedView = document.getElementById(viewId);
    if (selectedView) selectedView.classList.remove('hidden');
    
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const activeLink = document.querySelector(`[data-view="${viewId}"]`);
    if (activeLink) activeLink.classList.add('active');
}


// Pagespeed link

// Pagespeed link
const pagespeedLink = document.getElementById('pagespeed-link');
if (pagespeedLink) {
    pagespeedLink.addEventListener('click', (e) => {
        e.preventDefault();
        toggleModal('pagespeed-modal');
    });
}

// Status Pages link
const statusPagesLink = document.getElementById('status-pages-link');
if (statusPagesLink) {
    statusPagesLink.setAttribute('data-view', 'status-pages-view');
}

// ============================================
// 6. RENDER DASHBOARD TABLE
// ============================================
// Global store for filtering
window.monitorsData = [];

window.filterMonitorCards = function() {
    const searchVal = (document.getElementById('monitor-search')?.value || '').toLowerCase();
    const statusVal = document.getElementById('status-filter')?.value || 'all';
    const sortVal = document.getElementById('sort-filter')?.value || 'default';
    
    let filtered = window.monitorsData.filter(site => {
        const matchesSearch = (site.name && site.name.toLowerCase().includes(searchVal)) || 
                              (site.url && site.url.toLowerCase().includes(searchVal));
        const matchesStatus = statusVal === 'all' || site.status === statusVal;
        return matchesSearch && matchesStatus;
    });
    
    // Sort
    if (sortVal === 'response') {
        filtered.sort((a, b) => {
            const aRt = a.history?.length ? a.history[a.history.length-1].response_time || 99999 : 99999;
            const bRt = b.history?.length ? b.history[b.history.length-1].response_time || 99999 : 99999;
            return aRt - bRt;
        });
    } else if (sortVal === 'down') {
        filtered.sort((a, b) => {
            if (a.status === 'down' && b.status !== 'down') return -1;
            if (b.status === 'down' && a.status !== 'down') return 1;
            return 0;
        });
    } else if (sortVal === 'name') {
        filtered.sort((a, b) => (a.name || a.url).localeCompare(b.name || b.url));
    }
    
    renderCardsToDOM(filtered);
};

function renderDashboard(websites) {
    window.monitorsData = websites || [];
    
    // Calculate stats
    let upCount = 0;
    let downCount = 0;
    let pausedCount = 0;
    
    websites.forEach(site => {
        if (site.status === 'up') upCount++;
        else if (site.status === 'down') downCount++;
        else pausedCount++;
    });
    
    // Update top header monitor count
    const monitorCount = document.getElementById('monitor-count');
    if (monitorCount) {
        let dotColor = upCount > 0 ? '#22c55e' : (downCount > 0 ? '#ef4444' : '#3b82f6');
        monitorCount.innerHTML = `<span class="counter-dot" style="background:${dotColor};box-shadow:0 0 6px ${dotColor};"></span> ${websites.length} monitors <button class="badge-close-btn" style="background:none;border:none;color:#4b6880;margin-left:4px;cursor:pointer;" onclick="this.parentElement.style.display='none'">×</button>`;
    }
    
    // Update Right Analytics Panel
    const rpUp = document.getElementById('rp-up');
    const rpDown = document.getElementById('rp-down');
    const rpPaused = document.getElementById('rp-paused');
    const rpCountSub = document.getElementById('rp-count-sub');
    
    if (rpUp) rpUp.innerText = upCount;
    if (rpDown) rpDown.innerText = downCount;
    if (rpPaused) rpPaused.innerText = pausedCount;
    if (rpCountSub) rpCountSub.innerText = `Using ${websites.length} of 50 monitors.`;
    
    // Calculate Overall Uptime %
    let totalPct = 0;
    let sitesWithHistory = 0;
    websites.forEach(site => {
        if (site.history && site.history.length > 0) {
            let ups = site.history.filter(h => h.status === 'up').length;
            totalPct += (ups / site.history.length) * 100;
            sitesWithHistory++;
        }
    });
    const avgUptimeStr = sitesWithHistory > 0 ? (totalPct / sitesWithHistory).toFixed(2) + '%' : '100%';
    const rpUptime = document.getElementById('rp-uptime-pct');
    if (rpUptime) rpUptime.innerText = avgUptimeStr;
    
    // Render initially
    window.filterMonitorCards();
}

function renderCardsToDOM(filteredWebsites) {
    const container = document.getElementById('monitor-cards-container');
    if (!container) return; 
    
    const adminMode = document.getElementById('user-role') && document.getElementById('user-role').innerText === 'Super Admin';
    const listHeader = document.querySelector('.monitor-list-header');
    
    if (adminMode && listHeader && !listHeader.classList.contains('admin-grid')) {
        listHeader.style.gridTemplateColumns = "3fr 1.5fr 1fr 1fr 1fr 4fr 1fr";
        listHeader.classList.add('admin-grid');
        listHeader.innerHTML = `
            <div>Monitor</div>
            <div>Created By</div>
            <div style="text-align:center;">Status</div>
            <div>Response Time</div>
            <div>Interval</div>
            <div>Uptime History</div>
            <div style="text-align:right;">Actions</div>
        `;
    }
    
    if (filteredWebsites.length === 0) {
        container.innerHTML = `
            <div class="cards-empty">
              <p style="font-size:15px;margin-bottom:6px;">🚀 No monitors found</p>
              <p style="color:#2d4a62;">Adjust filters or click "Create new" to add one.</p>
            </div>
        `;
        return;
    }
    
    // Grouping by URL
    const grouped = {};
    filteredWebsites.forEach(site => {
        const u = site.url || 'unknown';
        if (!grouped[u]) grouped[u] = [];
        grouped[u].push(site);
    });
    
    let html = '';
    
    Object.keys(grouped).forEach(domain => {
        const sites = grouped[domain];
        const isGroup = sites.length > 1;
        
        sites.forEach((site, index) => {
            let statusClass = 'status-paused';
            let badgeClass = 'paused';
            let badgeText = 'PAUSED';
            if (site.status === 'up') { statusClass = 'status-up'; badgeClass = 'up'; badgeText = 'UP'; }
            else if (site.status === 'down') { statusClass = 'status-down'; badgeClass = 'down'; badgeText = 'DOWN'; }
            
            const lastCheck = site.history && site.history.length > 0 ? site.history[site.history.length - 1] : null;
            
            let barHtml = '';
            let histLen = site.history ? site.history.length : 0;
            let ups = 0;
            for (let i = 0; i < 30; i++) {
                let segClass = 'unknown';
                if (site.history && i < histLen) {
                    let h = site.history[histLen - 1 - i];
                    if (h.status === 'up') { segClass = 'up'; ups++; }
                    else if (h.status === 'down') segClass = 'down';
                }
                barHtml = `<div class="uptime-seg ${segClass}"></div>` + barHtml;
            }
            
            const sitePct = histLen > 0 ? ((ups / Math.min(histLen, 30)) * 100).toFixed(0) : 100;
            
            let dotColor = site.status === 'up' ? '#22c55e' : (site.status === 'down' ? '#ef4444' : '#eab308');
            let badgeIcon = site.status === 'up' ? '<i data-lucide="check" style="width:12px; height:12px; margin-right:4px;"></i>' : '<i data-lucide="x" style="width:12px; height:12px; margin-right:4px;"></i>';
            
            const gridStyle = adminMode ? "grid-template-columns: 3fr 1.5fr 1fr 1fr 1fr 4fr 1fr;" : "";
            
            let groupStyles = "";
            let nameHtml = `<div class="card-name" style="font-size:14px; font-weight:700; color:#fff;" title="${site.name || site.url}">${site.name || site.url}</div>
                            <div class="card-url" style="font-size:11px; color:#4d6a80; margin-top:2px;" title="${site.url}">${site.url}</div>`;
                            
            if (isGroup && adminMode) {
                if (index === 0) {
                    groupStyles = "border-bottom-left-radius: 0; border-bottom: none; margin-bottom: 0;";
                } else if (index === sites.length - 1) {
                    groupStyles = "border-top-left-radius: 0; border-top-right-radius: 0; background:rgba(8,14,30,0.4); box-shadow: inset 0 2px 5px rgba(0,0,0,0.2);";
                    nameHtml = `<div style="display:flex; align-items:center; color:#4d6a80; padding-left:15px;"><i data-lucide="corner-down-right" style="width:14px; height:14px; margin-right:8px;"></i> Grouped Replica</div>`;
                } else {
                    groupStyles = "border-radius: 0; border-bottom: none; background:rgba(8,14,30,0.4); box-shadow: inset 0 2px 5px rgba(0,0,0,0.2); margin-bottom: 0;";
                    nameHtml = `<div style="display:flex; align-items:center; color:#4d6a80; padding-left:15px;"><i data-lucide="corner-down-right" style="width:14px; height:14px; margin-right:8px;"></i> Grouped Replica</div>`;
                }
            }
            
            let ownerCol = adminMode ? `<div style="font-size:12px; font-weight:600; color:#8aafc8; display:flex; align-items:center;"><i data-lucide="user" style="width:12px; height:12px; margin-right:6px;"></i> ${site.owner_name || 'System Admin'}</div>` : '';
            
            html += `
            <div class="monitor-card ${statusClass}" style="cursor: pointer; ${gridStyle} ${groupStyles}" onclick="window.location.href='/monitors/${site.id}'">
              
              <div class="card-info" style="display:flex; align-items:flex-start; gap:8px;">
                <div style="color:${dotColor}; font-size:12px; margin-top:2px;">●</div>
                <div>${nameHtml}</div>
              </div>
              
              ${ownerCol}
              
              <div class="card-badge-col" style="display:flex; justify-content:center;">
                <span class="status-badge ${badgeClass}" style="padding: 4px 12px;">${badgeIcon} ${badgeText}</span>
              </div>
              
              <div class="card-meta" style="color:#c8d6e8; font-size:13px; justify-content:center; align-items:flex-start; min-width:auto;">
                ${lastCheck && lastCheck.response_time ? parseFloat(lastCheck.response_time).toFixed(2) + "ms" : "0ms"}
              </div>
    
              <div style="color:#c8d6e8; font-size:13px; display:flex; align-items:center; gap:6px;">
                <i data-lucide="clock" style="width:13px; height:13px; color:#8aafc8;"></i> ${site.check_interval} min
              </div>
              
              <div class="card-bar-col" style="display:flex; flex-direction:row; justify-content:space-between; align-items:center; width:100%;">
                <div class="uptime-bar" style="display:flex; gap:3px; flex:1; height:18px;">
                  ${barHtml}
                </div>
                <div class="uptime-pct" style="font-size:11px; color:#4d6a80; margin-left:8px;">${sitePct}%</div>
              </div>
              
              <div class="card-action" style="justify-self:end; display:flex; gap:6px;">
                <button class="btn-edit" style="padding:5px 12px; border-radius:6px; font-size:11px; background:rgba(255,255,255,0.05); color:#b8cfe0; border:1px solid rgba(255,255,255,0.1); cursor:pointer;" onmouseenter="this.style.background='rgba(255,255,255,0.08)';this.style.color='#fff';" onmouseleave="this.style.background='rgba(255,255,255,0.05)';this.style.color='#b8cfe0';" onclick="event.stopPropagation(); window.location.href='/monitors/${site.id}/edit'">Edit</button>
                <button class="btn-delete" style="padding:5px 12px; border-radius:6px; font-size:11px;" onmouseenter="this.style.boxShadow='0 0 10px rgba(239,68,68,0.2)'" onmouseleave="this.style.boxShadow='none'" onclick="event.stopPropagation(); deleteWebsite(${site.id})">Delete</button>
              </div>
              
            </div>
            `;
        });
    });
    
    container.innerHTML = html;
    if(window.lucide) {
        setTimeout(() => lucide.createIcons(), 50);
    }
}

// ============================================
// 7. DELETE WEBSITE
// ============================================
async function deleteWebsite(websiteId) {
    if (!confirm('Are you sure you want to delete this monitor?')) return;
    
    try {
        const res = await fetch(`${API_URL}/websites/${websiteId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
            loadDashboard(); // Reload dashboard
        } else {
            showError('Failed to delete monitor');
        }
    } catch (err) {
        console.error('Delete error:', err);
        showError('Error deleting monitor');
    }
}
window.deleteWebsite = deleteWebsite; // Expose globally

// ============================================
// 8. BULK IMPORT MODAL
// ============================================
function createBulkModal() {
    // Check if modal already exists
    if (document.getElementById('bulk-modal')) return;
    
    const modal = document.createElement('div');
    modal.id = 'bulk-modal';
    modal.className = 'fixed inset-0 bg-black/80 backdrop-blur-sm hidden items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-card border border-border rounded-xl p-6 w-[500px] shadow-2xl">
            <h3 class="text-lg font-bold text-white mb-1">Bulk Import Websites</h3>
            <p class="text-xs text-gray-400 mb-4">Enter URLs separated by commas or new lines</p>
            <form id="bulk-form" class="space-y-4 mt-4">
                <div>
                    <label class="text-xs font-medium text-gray-400 block mb-1.5">URLs</label>
                    <textarea id="bulk-urls" rows="8" class="w-full bg-bg border border-border rounded px-3 py-2 text-sm text-white focus:border-primary outline-none font-mono" placeholder="google.com&#10;github.com&#10;stackoverflow.com"></textarea>
                </div>
                <div id="bulk-result" class="hidden p-3 bg-bg border border-border rounded text-sm"></div>
                <div class="flex justify-end gap-3 mt-6">
                    <button type="button" onclick="toggleModal('bulk-modal')" class="px-4 py-2 text-xs font-medium text-gray-400 hover:text-white transition">Cancel</button>
                    <button type="submit" class="px-4 py-2 bg-primary hover:bg-blue-600 text-white text-xs font-medium rounded transition">Import</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Attach form handler
    const form = document.getElementById('bulk-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const urls = document.getElementById('bulk-urls').value;
            const resultDiv = document.getElementById('bulk-result');
            
            if (!urls.trim()) {
                resultDiv.classList.remove('hidden');
                resultDiv.className = 'p-3 bg-danger/10 border border-danger/20 rounded text-sm text-danger';
                resultDiv.innerText = 'Please enter at least one URL';
                return;
            }
            
            resultDiv.classList.remove('hidden');
            resultDiv.className = 'p-3 bg-bg border border-border rounded text-sm text-gray-400';
            resultDiv.innerText = 'Importing...';
            
            try {
                const res = await fetch(`${API_URL}/websites/bulk`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ urls: urls })
                });
                
                const data = await res.json();
                
                if (res.ok) {
                    resultDiv.className = 'p-3 bg-success/10 border border-success/20 rounded text-sm text-success';
                    resultDiv.innerText = data.message || 'Successfully imported websites';
                    document.getElementById('bulk-urls').value = '';
                    setTimeout(() => {
                        toggleModal('bulk-modal');
                        loadDashboard();
                    }, 1500);
                } else {
                    resultDiv.className = 'p-3 bg-danger/10 border border-danger/20 rounded text-sm text-danger';
                    resultDiv.innerText = data.detail || 'Failed to import websites';
                }
            } catch (err) {
                resultDiv.className = 'p-3 bg-danger/10 border border-danger/20 rounded text-sm text-danger';
                resultDiv.innerText = 'Network error: Could not reach the API';
            }
        });
    }
}

function toggleBulkModal() {
    if (!document.getElementById('bulk-modal')) {
        createBulkModal();
    }
    toggleModal('bulk-modal');
}
window.toggleBulkModal = toggleBulkModal; // Expose globally

// ============================================
// 9. PAGESPEED FORM HANDLER
// ============================================
const pagespeedForm = document.getElementById('pagespeed-form');
if (pagespeedForm) {
    pagespeedForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = document.getElementById('pagespeed-url').value;
        const resultDiv = document.getElementById('pagespeed-result');
        
        if (!url.trim()) return;
        
        resultDiv.classList.remove('hidden');
        resultDiv.className = 'p-4 bg-bg border border-border rounded text-sm';
        resultDiv.innerHTML = '<div class="text-gray-400">⏳ Checking speed...</div>';
        
        try {
            const res = await fetch(`${API_URL}/pagespeed?url=${encodeURIComponent(url)}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            
            if (res.ok) {
                const statusColor = data.status_code >= 200 && data.status_code < 300 ? 'text-success' : 'text-warning';
                const timeColor = data.response_time_ms < 500 ? 'text-success' : data.response_time_ms < 2000 ? 'text-warning' : 'text-danger';
                
                resultDiv.className = 'p-4 bg-success/10 border border-success/20 rounded text-sm';
                resultDiv.innerHTML = `
                    <div class="space-y-2">
                        <div class="flex items-center gap-2">
                            <span class="text-lg">✅</span>
                            <span class="text-white font-semibold">PageSpeed Check Complete</span>
                        </div>
                        <div class="pt-2 border-t border-border/50 space-y-2">
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">HTTP Status:</span>
                                <span class="font-medium ${statusColor}">${data.status_code || 'N/A'}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">Response Time:</span>
                                <span class="font-medium ${timeColor}">${data.response_time_ms ? Math.round(data.response_time_ms) : 'N/A'}ms</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-gray-400">URL:</span>
                                <span class="text-white text-xs font-mono">${data.url || url}</span>
                            </div>
                        </div>
                        <div class="pt-2 border-t border-border/50">
                            <p class="text-gray-300 text-xs">${data.message || 'Check completed successfully.'}</p>
                        </div>
                    </div>
                `;
            } else {
                resultDiv.className = 'p-4 bg-danger/10 border border-danger/20 rounded text-sm';
                resultDiv.innerHTML = `
                    <div class="space-y-2">
                        <div class="flex items-center gap-2">
                            <span class="text-lg">❌</span>
                            <span class="text-danger font-semibold">PageSpeed Check Failed</span>
                        </div>
                        <p class="text-gray-300 text-xs mt-2">${data.detail || data.message || 'Unknown error occurred'}</p>
                    </div>
                `;
            }
        } catch (err) {
            resultDiv.className = 'p-4 bg-danger/10 border border-danger/20 rounded text-sm';
            resultDiv.innerHTML = `
                <div class="space-y-2">
                    <div class="flex items-center gap-2">
                        <span class="text-lg">⚠️</span>
                        <span class="text-danger font-semibold">Network Error</span>
                    </div>
                    <p class="text-gray-300 text-xs mt-2">Could not reach the PageSpeed API. Please check your connection and try again.</p>
                </div>
            `;
        }
    });
}

// ============================================
// 10. ADD MONITOR FORM HANDLER
// ============================================
const addForm = document.getElementById('add-form');
if (addForm) {
    addForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const name = document.getElementById('site-name').value;
        const url = document.getElementById('site-url').value;
        const interval = parseInt(document.getElementById('site-interval').value) || 5;
        
        if (!url.trim()) {
            showWarning('Please enter a URL');
            return;
        }
        
        let cleanUrl = url.trim();
        if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
            cleanUrl = 'https://' + cleanUrl;
        }
        
        try {
            // Rule 6: Frontend validation before creating monitor
            const checkRes = await fetch(`${API_URL}/websites/check?domain=${encodeURIComponent(cleanUrl)}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const checkData = await checkRes.json();
            if (checkData.exists) {
                showError("Domain already being monitored by you");
                return;
            }
        
            const res = await fetch(`${API_URL}/websites/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name || cleanUrl.split('//')[1].split('/')[0],
                    url: cleanUrl,
                    check_interval: interval
                })
            });
            
            if (res.ok) {
                toggleModal('add-modal');
                addForm.reset();
                loadDashboard();
                showSuccess('Monitor created successfully');
            } else {
                const data = await res.json();
                showError(data.detail || 'Failed to create monitor');
            }
        } catch (err) {
            console.error('Add monitor error:', err);
            showError('Error creating monitor');
        }
    });
}

// ============================================
// 11. INFRASTRUCTURE VIEW LOADER
// ============================================
async function loadInfrastructureView() {
    try {
        const siteRes = await fetch(`${API_URL}/websites/`, { 
            headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        if (!siteRes.ok) return;
        
        const websites = await siteRes.json();
        const totalMonitors = websites.length;
        const activeChecks = websites.filter(s => s.status === 'up').length;
        
        // Calculate average response time
        let totalResponseTime = 0;
        let responseCount = 0;
        websites.forEach(site => {
            if (site.history && site.history.length > 0) {
                const lastCheck = site.history[site.history.length - 1];
                if (lastCheck && lastCheck.response_time) {
                    totalResponseTime += lastCheck.response_time;
                    responseCount++;
                }
            }
        });
        const avgResponse = responseCount > 0 ? Math.round(totalResponseTime / responseCount) : 0;
        
        // Calculate uptime percentage
        const upCount = websites.filter(s => s.status === 'up').length;
        const uptimePercent = totalMonitors > 0 ? Math.round((upCount / totalMonitors) * 100) : 100;
        
        // Get checks today (estimate based on check interval)
        const checksToday = totalMonitors * (24 * 60 / 5); // Assuming 5 min interval
        
        // Update UI
        const totalMonitorsEl = document.getElementById('infra-total-monitors');
        const activeChecksEl = document.getElementById('infra-active-checks');
        const avgResponseEl = document.getElementById('infra-avg-response');
        const checksTodayEl = document.getElementById('infra-checks-today');
        const uptimeEl = document.getElementById('infra-uptime');
        const lastCheckEl = document.getElementById('infra-last-check');
        const activityListEl = document.getElementById('infra-activity-list');
        
        if (totalMonitorsEl) totalMonitorsEl.innerText = totalMonitors;
        if (activeChecksEl) activeChecksEl.innerText = activeChecks;
        if (avgResponseEl) avgResponseEl.innerText = `${avgResponse}ms`;
        if (checksTodayEl) checksTodayEl.innerText = checksToday.toLocaleString();
        if (uptimeEl) uptimeEl.innerText = `${uptimePercent}%`;
        
        // Get last check time
        let lastCheckTime = null;
        websites.forEach(site => {
            if (site.last_checked) {
                const checkTime = new Date(site.last_checked);
                if (!lastCheckTime || checkTime > lastCheckTime) {
                    lastCheckTime = checkTime;
                }
            }
        });
        
        if (lastCheckEl) {
            if (lastCheckTime) {
                const now = new Date();
                const diff = Math.floor((now - lastCheckTime) / 1000 / 60);
                if (diff < 1) lastCheckEl.innerText = 'Just now';
                else if (diff < 60) lastCheckEl.innerText = `${diff} min ago`;
                else lastCheckEl.innerText = `${Math.floor(diff / 60)} hour${Math.floor(diff / 60) > 1 ? 's' : ''} ago`;
            } else {
                lastCheckEl.innerText = 'Never';
            }
        }
        
        // Show recent activity
        if (activityListEl) {
            if (websites.length === 0) {
                activityListEl.innerHTML = '<p class="text-sm text-gray-500">No monitors configured yet.</p>';
            } else {
                let html = '';
                websites.slice(0, 5).forEach(site => {
                    const statusColor = site.status === 'up' ? 'text-success' : 'text-danger';
                    const statusText = site.status === 'up' ? 'UP' : 'DOWN';
                    html += `<div class="flex justify-between items-center p-2 border-b border-border/50">
                        <span class="text-sm text-white">${site.name || site.url}</span>
                        <span class="text-xs font-medium ${statusColor}">${statusText}</span>
                    </div>`;
                });
                activityListEl.innerHTML = html;
            }
        }
    } catch (err) {
        console.error('Infrastructure view error:', err);
    }
}

// ============================================
// 12. NOTIFICATIONS VIEW LOADER
// ============================================
async function loadNotificationsView() {
    try {
        const [recentRes, errorsRes] = await Promise.all([
            fetch(`${API_URL}/notifications/recent`, { headers: { 'Authorization': `Bearer ${token}` } }),
            fetch(`${API_URL}/notifications/common-errors`, { headers: { 'Authorization': `Bearer ${token}` } })
        ]);
        
        const errorsListEl = document.getElementById('notifications-errors-list');
        const notificationsListEl = document.getElementById('notifications-list');
        
        // Load common errors
        if (errorsRes.ok && errorsListEl) {
            const commonErrors = await errorsRes.json();
            if (commonErrors.length === 0) {
                errorsListEl.innerHTML = '<p class="text-sm text-gray-500">No errors found. All systems operational! 🎉</p>';
            } else {
                let html = '';
                commonErrors.forEach(e => {
                    html += `<div class="flex justify-between items-center p-3 bg-danger/10 border border-danger/20 rounded mb-2">
                        <span class="text-sm text-gray-300">${e.error || 'Unknown error'}</span>
                        <span class="text-xs font-medium text-danger bg-danger/20 px-2 py-1 rounded">${e.count} time${e.count !== 1 ? 's' : ''}</span>
                    </div>`;
                });
                errorsListEl.innerHTML = html;
            }
        } else if (errorsListEl) {
            errorsListEl.innerHTML = '<p class="text-sm text-gray-500">Loading errors...</p>';
        }
        
        // Load recent notifications (both UP and DOWN)
        if (recentRes.ok && notificationsListEl) {
            const notifications = await recentRes.json();
            if (notifications.length === 0) {
                notificationsListEl.innerHTML = '<p class="text-sm text-gray-500">No notifications yet. You\'ll see alerts here when your monitors change status.</p>';
            } else {
                let html = '';
                notifications.slice(0, 20).forEach(notif => {
                    const statusColor = notif.is_up ? 'text-success' : 'text-danger';
                    const bgColor = notif.is_up ? 'bg-success/10 border-success/20' : 'bg-danger/10 border-danger/20';
                    const statusIcon = notif.is_up ? '✅' : '🔴';
                    
                    html += `<div class="p-4 bg-card border ${bgColor} rounded-lg mb-3 hover:shadow-lg transition-shadow">
                        <div class="flex justify-between items-start mb-2">
                            <div class="flex items-center gap-2">
                                <span class="text-lg">${statusIcon}</span>
                                <div>
                                    <span class="text-sm font-semibold text-white">${notif.website_name || 'Unknown'}</span>
                                    <span class="ml-2 text-xs ${statusColor} font-medium">${notif.status || 'UNKNOWN'}</span>
                                </div>
                            </div>
                            <span class="text-xs text-gray-500">${notif.time || 'Unknown time'}</span>
                        </div>
                        <p class="text-sm text-gray-300 mb-1">${notif.message || 'No details available'}</p>
                        ${notif.website_url ? `<p class="text-xs text-gray-500">${notif.website_url}</p>` : ''}
                        ${notif.response_time ? `<p class="text-xs text-gray-500 mt-1">Response time: ${Math.round(notif.response_time)}ms</p>` : ''}
                    </div>`;
                });
                notificationsListEl.innerHTML = html;
            }
        } else if (notificationsListEl) {
            notificationsListEl.innerHTML = '<p class="text-sm text-gray-500">Loading notifications...</p>';
        }
    } catch (err) {
        console.error('Notifications view error:', err);
        const errorsListEl = document.getElementById('notifications-errors-list');
        const notificationsListEl = document.getElementById('notifications-list');
        if (errorsListEl) errorsListEl.innerHTML = '<p class="text-sm text-danger">Failed to load errors. Please try again.</p>';
        if (notificationsListEl) notificationsListEl.innerHTML = '<p class="text-sm text-danger">Failed to load notifications. Please try again.</p>';
    }
}

// ============================================
// 13. INCIDENTS VIEW LOADER
// ============================================
async function loadIncidentsView() {
    try {
        const incidentsRes = await fetch(`${API_URL}/notifications/incidents`, { 
            headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        const incidentListEl = document.getElementById('incident-list');
        if (!incidentListEl) return;
        
        if (incidentsRes.ok) {
            const incidents = await incidentsRes.json();
            if (incidents.length === 0) {
                incidentListEl.innerHTML = `
                    <div class="p-6 bg-card border border-border rounded-lg text-center">
                        <p class="text-lg text-success mb-2">🎉 All Systems Operational!</p>
                        <p class="text-sm text-gray-500">No incidents recorded. Great job keeping everything up!</p>
                    </div>
                `;
            } else {
                let html = '';
                incidents.forEach(inc => {
                    html += `<div class="p-4 bg-card border border-danger/30 rounded-lg hover:border-danger/50 transition-colors mb-3">
                        <div class="flex justify-between items-start mb-2">
                            <div class="flex items-center gap-2">
                                <span class="text-xl">🔴</span>
                                <div>
                                    <span class="px-2 py-1 text-xs font-bold bg-danger/10 text-danger border border-danger/20 rounded">${inc.status || 'DOWN'}</span>
                                    <span class="ml-2 text-sm font-semibold text-white">${inc.website_name || 'Unknown Website'}</span>
                                </div>
                            </div>
                            <span class="text-xs text-gray-500">${inc.time || 'Unknown time'}</span>
                        </div>
                        <p class="text-sm text-gray-300 mt-2 mb-1">${inc.message || 'No details available'}</p>
                        ${inc.website_url ? `<p class="text-xs text-gray-500">URL: ${inc.website_url}</p>` : ''}
                        ${inc.status_code ? `<p class="text-xs text-gray-500 mt-1">HTTP Status: ${inc.status_code}</p>` : ''}
                        ${inc.error ? `<p class="text-xs text-danger mt-1">Error: ${inc.error}</p>` : ''}
                    </div>`;
                });
                incidentListEl.innerHTML = html;
            }
        } else {
            incidentListEl.innerHTML = '<p class="text-sm text-danger">Failed to load incidents. Please try again.</p>';
        }
    } catch (err) {
        console.error('Incidents view error:', err);
        const incidentListEl = document.getElementById('incident-list');
        if (incidentListEl) incidentListEl.innerHTML = '<p class="text-sm text-danger">Error loading incidents. Please check your connection.</p>';
    }
}

// ============================================
// 14. STATUS PAGES VIEW LOADER
// ============================================
async function loadStatusPagesView() {
    const statusPagesListEl = document.getElementById('status-pages-list');
    if (!statusPagesListEl) return;
    
    // For now, show a placeholder message
    // In the future, this would fetch status pages from the backend
    statusPagesListEl.innerHTML = `
        <div class="p-4 bg-card border border-border rounded-lg">
            <p class="text-sm text-gray-400 mb-2">Status pages feature is coming soon!</p>
            <p class="text-xs text-gray-500">This feature will allow you to create public status pages that display the current status of your monitored services.</p>
        </div>
    `;
}

// ============================================
// 15. ADMIN LOGS FETCHER
// ============================================
async function fetchAdminLogs() {
    const output = document.getElementById('admin-logs-output');
    if (!output) return;
    
    output.innerText = 'Fetching all logs and users...';
    
    try {
        const [logsRes, usersRes] = await Promise.all([
            fetch(`${API_URL}/admin/logs`, { headers: { 'Authorization': `Bearer ${token}` } }),
            fetch(`${API_URL}/admin/users`, { headers: { 'Authorization': `Bearer ${token}` } })
        ]);
        
        if (logsRes.ok && usersRes.ok) {
            const logs = await logsRes.json();
            const users = await usersRes.json();
            
            output.innerText = `USERS (${users.length}):\n` + JSON.stringify(users, null, 2) + `\n\n--- LOGS (last 100):\n` + JSON.stringify(logs, null, 2);
        } else {
            output.innerText = 'ERROR: Failed to fetch admin data. Check API/Permissions.';
        }
    } catch (e) {
        output.innerText = 'ERROR: Failed to fetch admin data. Check API/Permissions.';
        console.error(e);
    }
}
window.fetchAdminLogs = fetchAdminLogs; // Expose globally

// ============================================
// 12. MAIN DASHBOARD LOADER
// ============================================
async function loadDashboard() {
    try {
        // Fetch user info
        const userRes = await fetch(`${API_URL}/auth/me`, { 
            headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        if (!userRes.ok) {
            throw new Error('Auth failed');
        }
        
        currentUser = await userRes.json();
        
        // Update user display
        const displayName = currentUser.name || currentUser.email.split('@')[0];
        const initials = displayName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        
        const userRoleEl = document.getElementById('user-role');
        const userAvatarEl = document.getElementById('user-avatar');
        const greetingEl = document.getElementById('greeting-name-display');
        const userNameEl = document.getElementById('user-name');
        const bulkBtnContainer = document.getElementById('admin-actions-container');
        const adminBadge = document.getElementById('admin-badge');
        
        // Update standard info
        if (userRoleEl) userRoleEl.innerText = 'Team Member'; // Default
        if (greetingEl) greetingEl.innerText = displayName;
        if (userAvatarEl) userAvatarEl.innerText = initials;
        if (userNameEl) userNameEl.innerText = displayName;

        // Check & force admin display
        if (currentUser.role === 'admin') {
            if (userRoleEl) userRoleEl.innerText = 'Super Admin';
            if (adminBadge) adminBadge.classList.remove('hidden');
            
            // Create Bulk Import button if needed
            if (bulkBtnContainer && !document.getElementById('bulk-btn')) {
                const btn = document.createElement('button');
                btn.id = 'bulk-btn';
                btn.className = 'px-3 py-1.5 bg-card border border-border hover:bg-hover text-gray-300 text-xs font-medium rounded transition-colors mr-2 shadow-sm';
                btn.innerText = 'Bulk Import';
                btn.onclick = toggleBulkModal;
                bulkBtnContainer.prepend(btn);
                
                // Ensure Bulk Modal HTML exists
                if (!document.getElementById('bulk-modal')) {
                    createBulkModal();
                }
            }
        } else {
            if (adminBadge) adminBadge.classList.add('hidden');
            const bulkBtn = document.getElementById('bulk-btn');
            if (bulkBtn) bulkBtn.remove();
        }
        
        // Fetch and render websites
        const siteRes = await fetch(`${API_URL}/websites/`, { 
            headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        if (siteRes.ok) {
        const websites = await siteRes.json();
            renderDashboard(websites);
        } else {
            console.error('Failed to fetch websites');
        }

    } catch (err) {
        console.error("Dashboard Load Error:", err);
        if (!token) {
            window.location.href = '../index.html';
        }
    }
}

// ============================================
// 16. CHAT FORM HANDLER (Optional Feature)
// ============================================
const chatForm = document.getElementById('chat-form');
if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = document.getElementById('chat-input');
        const messagesContainer = document.getElementById('chat-messages');
        
        if (!input || !messagesContainer) return;
        
        const message = input.value.trim();
        if (!message) return;
        
        // Add user message
        const userMsg = document.createElement('div');
        userMsg.className = 'flex justify-end';
        userMsg.innerHTML = `<div class="p-2 rounded-lg max-w-[80%] text-xs bg-primary text-white">${message}</div>`;
        messagesContainer.appendChild(userMsg);
        
        input.value = '';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Simple mock response
        setTimeout(() => {
            const botMsg = document.createElement('div');
            botMsg.className = 'flex justify-start';
            botMsg.innerHTML = `<div class="p-2 rounded-lg max-w-[80%] text-xs bg-blue-500/10 text-blue-300">I'm a simple assistant. For help, check the sidebar links or use the Pagespeed feature.</div>`;
            messagesContainer.appendChild(botMsg);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 500);
    });
}

// ============================================
// 17. INITIALIZATION
// ============================================
// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        loadDashboard();
    });
} else {
loadDashboard();
}

    // Poll for updates every 5 seconds
    setInterval(loadDashboard, 5000);

})();
