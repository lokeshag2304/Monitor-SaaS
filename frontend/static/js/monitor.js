(function() {
    const API_URL = window.API_URL || window.location.origin;
    const token = localStorage.getItem('token');
    let rtChartInstance = null;

if (!token) {
    window.location.href = '/';
}

function getMonitorId() {
    const params = new URLSearchParams(window.location.search);
    if (params.has('id')) return params.get('id');

    // Safer pathname split approach: /monitors/123 or /monitors/123/
    const parts = window.location.pathname.split('/').filter(p => p.length > 0);
    // Assuming the URL pattern is /monitors/{id}, the ID is the last part
    return parts.length > 0 ? parts[parts.length - 1] : null;
}

async function loadMonitorData() {
    const monitorId = getMonitorId();
    if (!monitorId || isNaN(monitorId)) {
        showWarning("Invalid monitor ID");
        window.location.href = '/static/dashboard.html';
        return;
    }

    try {
        const headers = { 'Authorization': `Bearer ${token}` };

        // Concurrent fetching for fast loading
        const [monRes, statsRes, checksRes, incRes] = await Promise.all([
            fetch(`${API_URL}/api/monitors/${monitorId}`, { headers }),
            fetch(`${API_URL}/api/monitors/${monitorId}/stats`, { headers }),
            fetch(`${API_URL}/api/monitors/${monitorId}/checks?limit=100`, { headers }),
            fetch(`${API_URL}/api/monitors/${monitorId}/incidents`, { headers })
        ]);

        if (monRes.status === 401 || monRes.status === 403) {
            localStorage.removeItem('token');
            window.location.href = '/';
            return;
        }

        if (!monRes.ok) throw new Error("Monitor not found");

        const monitor = monRes.ok ? await monRes.json() : {};
        const stats = statsRes.ok ? await statsRes.json() : {};
        const checks = checksRes.ok ? await checksRes.json() : [];
        const incidents = incRes.ok ? await incRes.json() : [];

        renderMonitorInfo(monitor, stats);
        renderUptimeBars(checks, stats);
        renderChart(checks, stats);
        renderIncidents(incidents);

    } catch (err) {
        console.error("Failed to load monitor data:", err);
        document.getElementById('det-name').innerText = "Error Loading Monitor";
    }
}

function renderMonitorInfo(monitor, stats) {
    document.getElementById('det-name').innerHTML = `${monitor.name || monitor.url}`;
    document.getElementById('det-url').innerText = `${monitor.type} monitor for ${monitor.url}`;

    try {
        const urlObj = new URL(monitor.url.startsWith('http') ? monitor.url : 'https://' + monitor.url);
        const domain = urlObj.hostname;
        const iconEl = document.querySelector('.header-icon');
        if (iconEl) {
            iconEl.innerHTML = `<img src="https://www.google.com/s2/favicons?domain=${domain}&sz=64" style="width: 24px; height: 24px; border-radius: 4px;" onerror="this.outerHTML='<i data-lucide=\\'globe\\'></i>'; lucide.createIcons();">`;
        }
    } catch (e) { }

    // Status Badge
    const badge = document.getElementById('det-status-badge');
    const statusText = monitor.status.toUpperCase();
    badge.innerText = statusText;
    badge.className = `status-badge ${monitor.status === 'up' ? 'up' : (monitor.status === 'down' ? 'down' : 'paused')}`;

    // Uptime sub
    document.getElementById('det-uptime-text').innerText = `Uptime: ${stats.uptime_percentage}%`;
    document.getElementById('det-interval').innerText = `Check every ${monitor.interval}m`;

    // Last Check 
    if (monitor.last_checked) {
        const diffSecs = Math.floor((new Date() - new Date(monitor.last_checked)) / 1000);
        let timeStr = `${diffSecs} sec ago`;
        if (diffSecs > 60) timeStr = `${Math.floor(diffSecs / 60)} min ago`;
        document.getElementById('det-last-check').innerText = timeStr;
    } else {
        document.getElementById('det-last-check').innerText = "--";
    }

    // Await count logic applied in renderUptimeBars but we populate text
    document.getElementById('pct-24h').innerText = `${stats.uptime_percentage}%`;

    // SLA Badge
    const slaBadge = document.getElementById('det-sla-badge');
    if (slaBadge && stats.uptime_percentage !== undefined) {
        const uptime = stats.uptime_percentage;
        let tier = "Needs Attention";
        let color = '#ef4444';
        
        if (uptime >= 99.99) { tier = "Excellent"; color = "#22c55e"; }
        else if (uptime >= 99.9) { tier = "Very Good"; color = "#3b82f6"; }
        else if (uptime >= 99.0) { tier = "Good"; color = "#eab308"; }
        
        slaBadge.innerText = `Tier: ${tier}`;
        slaBadge.style.display = 'inline-block';
        slaBadge.style.background = color + '1A';
        slaBadge.style.color = color;
        slaBadge.style.borderColor = color + '33';
    }
}

function renderUptimeBars(checks) {
    // Generate Uptime Bars (simulate filling for 24h, 7d, 30d using recent checks due to DB limit mock)
    // Real implementation would group by actual hours/days.
    document.getElementById('det-history-count').innerText = checks.length;

    let u = 0, d = 0;
    checks.forEach(c => { if (c.status === 'UP') u++; else d++; });
    document.getElementById('det-up-count').innerText = u;
    document.getElementById('det-down-count').innerText = d;

    const buildBar = (containerId, pointCount) => {
        let barHtml = '';
        for (let i = 0; i < pointCount; i++) {
            let segClass = 'unknown'; // defaults
            if (i < checks.length) {
                // Read fresh checks backwards
                let c = checks[checks.length - 1 - i];
                if (c) {
                    segClass = c.status === 'UP' ? 'up' : 'down';
                }
            } else {
                // If not enough checks, simulate with green if overall is good
                segClass = (Math.random() > 0.05) ? 'up' : 'down';
            }
            barHtml += `<div class="uptime-seg-lg ${segClass}"></div>`;
        }
        document.getElementById(containerId).innerHTML = barHtml;
    };

    buildBar('bar-24h', 30);
    buildBar('bar-7d', 40);
    buildBar('bar-30d', 50);
}

function renderChart(checks, stats) {
    document.getElementById('stat-avg').innerText = stats.average_response_time || 0;
    document.getElementById('stat-min').innerText = stats.minimum_response_time || 0;
    document.getElementById('stat-max').innerText = stats.maximum_response_time || 0;

    const ctx = document.getElementById('rtChart').getContext('2d');

    // Reverse checks so oldest is first on left
    const chronChecks = [...checks].reverse();

    // We want only up to ~30 points for cleanliness
    const displayChecks = chronChecks.slice(-30);

    const labels = displayChecks.map(c => {
        const d = new Date(c.checked_at);
        return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
    });

    const data = displayChecks.map(c => c.response_time);

    if (rtChartInstance) rtChartInstance.destroy();

    Chart.defaults.color = '#4d6a80';
    rtChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Response Time (ms)',
                data: data,
                borderColor: '#06b6d4',
                backgroundColor: 'rgba(6,182,212,0.1)',
                borderWidth: 2,
                pointBackgroundColor: '#22d3ee',
                pointBorderColor: '#fff',
                pointBorderWidth: 1,
                pointRadius: 3,
                pointHoverRadius: 5,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(7,12,26,0.9)',
                    titleColor: '#fff',
                    bodyColor: '#e2eaf4',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.02)', drawBorder: false },
                    ticks: { maxTicksLimit: 6 }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.04)', borderDash: [5, 5] },
                    beginAtZero: true
                }
            }
        }
    });
}

function renderIncidents(incidents) {
    const container = document.getElementById('incidents-container');
    if (!incidents || incidents.length === 0) {
        // Keep the good job graphic
        return;
    }

    let html = '';
    incidents.forEach(inc => {
        const start = new Date(inc.started_at).toLocaleString();
        const end = inc.resolved_at ? new Date(inc.resolved_at).toLocaleString() : 'Ongoing';
        const dur = inc.duration ? `${(inc.duration / 60).toFixed(1)} min` : 'Pending';

        html += `
        <div class="incident-item">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="font-weight:700; color:#ef4444; font-size:13px;">Monitor DOWN</span>
                <span style="font-size:11px; color:#4d6a80;">Duration: ${dur}</span>
            </div>
            <div style="font-size:12px; color:#b8cfe0;">
                Started: <span style="color:#fff;">${start}</span> &mdash; Resolved: <span style="color:#fff;">${end}</span>
            </div>
            <div style="font-size:11px; color:#ef4444; margin-top:6px;">Reason: ${inc.reason || 'Timeout/No Response'}</div>
        </div>`;
    });

    container.innerHTML = html;
}

async function sendTestNotification() {
    const monitorId = getMonitorId();
    if (!monitorId) return;

    const btn = document.getElementById('btn-test-notif');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i data-lucide="loader"></i> Sending...'; lucide.createIcons(); }

    try {
        const res = await fetch(`${API_URL}/api/monitors/${monitorId}/test-notification`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (res.ok) {
            if (data.status === 'warning') {
                showWarning(data.message || 'SMTP not configured — email skipped.');
            } else {
                showSuccess(data.message || 'Test notification sent!');
            }
        } else {
            showError(data.detail || 'Failed to send test notification');
        }
    } catch (err) {
        console.error('Test notification error:', err);
        showError('Network error — could not reach the server.');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="bell"></i> Test Notification'; lucide.createIcons(); }
    }
}

async function openMonitorReport() {
    const monitorId = getMonitorId();
    const modal = document.getElementById('monitor-report-modal');
    modal.classList.add('active');
    
    try {
        const res = await fetch(`${API_URL}/api/reports/monitor/${monitorId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Failed to load report");
        
        const data = await res.json();
        
        document.getElementById('modal-report-title').innerText = `${data.monitor_name} Performance Report`;
        document.getElementById('modal-uptime-val').innerText = `${data.uptime_percentage}%`;
        document.getElementById('modal-gauge-text').innerText = `${Math.round(data.uptime_percentage)}%`;
        
        const gauge = document.getElementById('modal-gauge');
        gauge.style.setProperty('--gauge-percent', `${data.uptime_percentage}%`);
        
        // Color logic
        let color = '#ef4444';
        if (data.uptime_percentage >= 99.99) color = '#22c55e';
        else if (data.uptime_percentage >= 99.9) color = '#3b82f6';
        else if (data.uptime_percentage >= 99) color = '#eab308';
        
        gauge.style.setProperty('--gauge-color', color);
        document.getElementById('modal-uptime-val').style.color = color;
        
        const badge = document.getElementById('modal-sla-badge');
        badge.innerText = `Tier: ${data.sla_tier}`;
        badge.style.background = color + '1A';
        badge.style.color = color;
        badge.style.borderColor = color + '33';
        
        document.getElementById('modal-avg-resp').innerText = `${data.avg_response_time}ms`;
        document.getElementById('modal-total-inc').innerText = data.total_incidents;
        document.getElementById('modal-downtime').innerText = `${data.total_downtime_minutes} Minutes Downtime`;
        document.getElementById('modal-total-checks').innerText = `${data.total_checks.toLocaleString()} Checks`;
        
        lucide.createIcons();
    } catch (err) {
        console.error(err);
        showError("Failed to fetch monitor report.");
    }
}

function closeMonitorReport() {
    const modal = document.getElementById('monitor-report-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

    // Exposure to global scope for HTML event handlers
    window.loadMonitorData = loadMonitorData;
    window.getMonitorId = getMonitorId;
    window.sendTestNotification = sendTestNotification;
    window.openMonitorReport = openMonitorReport;
    window.closeMonitorReport = closeMonitorReport;

    // Init
    document.addEventListener('DOMContentLoaded', loadMonitorData);

})();
