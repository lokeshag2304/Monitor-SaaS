(function() {
    const API_URL = window.API_URL || window.location.origin;
    const token = localStorage.getItem('token');
    let rtChartInstance = null;
    let checkTimer = null;
    let userMapInstance = null;

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
            fetch(`${API_URL}/api/monitors/${monitorId}/checks?hours=24`, { headers }),
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
        
        // Only init map once
        if (!userMapInstance) {
            initUserMap();
        }

    } catch (err) {
        console.error("Failed to load monitor data:", err);
        document.getElementById('det-name').innerText = "Error Loading Monitor";
    }
}

/**
 * Utility to parse timestamps from backend (UTC) correctly and convert to local Date
 */
function parseUTCDate(dateStr) {
    if (!dateStr) return null;
    // If it doesn't have a timezone indicator, assume it's UTC and append 'Z'
    if (!dateStr.includes('Z') && !dateStr.includes('+')) {
        // Handle both T and space separators
        return new Date(dateStr.replace(' ', 'T') + 'Z');
    }
    return new Date(dateStr);
}

function formatCheckDate(dateStr) {
    if (!dateStr) return "Never";
    const date = parseUTCDate(dateStr);
    if (!date || isNaN(date.getTime())) return "Invalid Date";
    
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[date.getMonth()];
    const day = date.getDate();
    let hours = date.getHours();
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    return `${month} ${day}, ${hours}:${minutes} ${ampm}`;
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
    const uptimeText = (stats.uptime_percentage !== null && stats.uptime_percentage !== undefined) ? `${stats.uptime_percentage}%` : "--";
    document.getElementById('det-uptime-text').innerText = `Uptime: ${uptimeText}`;
    document.getElementById('det-interval').innerText = `Check every ${monitor.interval}m`;

    // Last Check 
    // Initialized by startLastCheckTimer(monitor.interval)
    const lastCheckSub = document.querySelector("#det-last-check + p");
    if (lastCheckSub) {
        const totalChecks = (stats.total_checks || 0).toLocaleString();
        const lastCheckedFormatted = formatCheckDate(monitor.last_checked);
        lastCheckSub.innerHTML = `<span id="det-history-count">${totalChecks}</span> checks analyzed • Last checked: ${lastCheckedFormatted}`;
    }

    // Await count logic applied in renderUptimeBars but we populate text
    document.getElementById('pct-24h').innerText = (stats.uptime_percentage !== null && stats.uptime_percentage !== undefined) ? `${stats.uptime_percentage}%` : "--";

    // SLA Badge
    const slaBadge = document.getElementById('det-sla-badge');
    if (slaBadge) {
        if (stats.uptime_percentage !== null && stats.uptime_percentage !== undefined) {
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
        } else {
            slaBadge.style.display = 'none';
        }
    }

    // Region / Monitoring Location
    const monRegionEl = document.getElementById('mon-region-text');
    if (monRegionEl) {
        monRegionEl.innerText = monitor.region || "Default / Global";
    }

    // Pause button update
    const pauseBtn = document.getElementById('pause-btn');
    if (pauseBtn) {
        if (monitor.status === 'paused') {
            pauseBtn.innerHTML = '<i data-lucide="play"></i> Resume';
        } else {
            pauseBtn.innerHTML = '<i data-lucide="pause"></i> Pause';
        }
        lucide.createIcons();
    }

    // Uptime Duration Logic
    if (window.uptimeInterval) clearInterval(window.uptimeInterval);
    const durationEl = document.getElementById("det-uptime-duration");
    if (durationEl) {
        const currentStatus = monitor.status ? monitor.status.toLowerCase() : "";
        if (currentStatus === 'up' && monitor.up_since) {
            const upSince = parseUTCDate(monitor.up_since);
            const updateTimer = () => {
                const now = new Date();
                const diff = Math.floor((now - upSince) / 1000);
                if (diff < 0) return;

                const hours = Math.floor(diff / 3600);
                const minutes = Math.floor((diff % 3600) / 60);
                const seconds = diff % 60;
                
                let timeStr = "";
                if (hours > 0) timeStr += `${hours}h `;
                if (minutes > 0 || hours > 0) timeStr += `${minutes}m `;
                timeStr += `${seconds}s`;
                
                durationEl.innerHTML = `<i data-lucide="clock" style="width:12px; height:12px; display:inline-block; vertical-align:middle; margin-right:4px;"></i> Currently up for ${timeStr}`;
                lucide.createIcons();
            };
            updateTimer();
            window.uptimeInterval = setInterval(updateTimer, 1000);
        } else {
            durationEl.innerText = "";
        }
    }

    // Start the last check timer
    if (monitor.interval) {
        startLastCheckTimer(monitor.interval, monitor.last_checked);
    }
    lucide.createIcons();
}

function startLastCheckTimer(intervalMinutes, lastChecked) {
    if (!lastChecked) {
        const lastCheckEl = document.getElementById("det-last-check");
        if (lastCheckEl) lastCheckEl.innerText = "--";
        return;
    }

    const lastCheckedDate = parseUTCDate(lastChecked);
    const maxSeconds = intervalMinutes * 60;

    if (checkTimer) clearInterval(checkTimer);

    const updateUI = () => {
        const now = new Date();
        const elapsedSecs = Math.floor((now - lastCheckedDate) / 1000);
        
        // Calculate display time based on elapsed time % interval to handle the reset
        const displaySecs = elapsedSecs % maxSeconds;

        const mins = Math.floor(displaySecs / 60);
        const secs = displaySecs % 60;
        const formatted = `${mins}:${secs.toString().padStart(2, "0")}`;

        const lastCheckEl = document.getElementById("det-last-check");
        if (lastCheckEl) {
            lastCheckEl.innerText = formatted;
        }
    };

    updateUI(); 
    checkTimer = setInterval(updateUI, 1000);
}

function renderUptimeBars(checks, stats) {
    // Generate Uptime Bars based on actual checks
    document.getElementById('det-up-count-24h').innerText = stats.up_count_24h || 0;
    document.getElementById('det-down-count-24h').innerText = stats.down_count_24h || 0;
    document.getElementById('det-paused-count-24h').innerText = stats.paused_count_24h || 0;

    const buildBar = (containerId, limit) => {
        let barHtml = '';
        // Use all available checks up to limit
        const relevantChecks = checks.slice(0, limit).reverse(); 
        
        relevantChecks.forEach(c => {
            const segClass = (c.status || "").toLowerCase();
            barHtml += `<div class="uptime-seg-lg ${segClass}"></div>`;
        });

        // Fill with unknown if we have fewer than 30 points for better visual
        const minPoints = 30;
        if (relevantChecks.length < minPoints) {
            for (let i = 0; i < (minPoints - relevantChecks.length); i++) {
                barHtml = `<div class="uptime-seg-lg unknown"></div>` + barHtml;
            }
        }
        
        document.getElementById(containerId).innerHTML = barHtml;
    };

    buildBar('bar-24h', 300); // 24h at 5m interval is 288 checks
    buildBar('bar-7d', 100); 
    buildBar('bar-30d', 100);
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
        const d = parseUTCDate(c.checked_at);
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
        const startRaw = parseUTCDate(inc.started_at);
        const start = startRaw ? startRaw.toLocaleString() : 'N/A';
        const endRaw = inc.resolved_at ? parseUTCDate(inc.resolved_at) : null;
        const end = endRaw ? endRaw.toLocaleString() : 'Ongoing';
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

async function togglePause() {
    const monitorId = getMonitorId();
    if (!monitorId) return;

    try {
        const res = await fetch(`${API_URL}/api/monitors/${monitorId}/toggle-pause`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!res.ok) throw new Error("Failed to toggle pause");
        
        const data = await res.json();

        if (data.status === "paused") {
            showWarning("Monitor paused");
        } else {
            showSuccess("Monitor resumed");
        }

        loadMonitorData();
    } catch (err) {
        console.error('Toggle pause error:', err);
        showError('Network error — could not reach the server.');
    }
}

async function loadMonitorReport(monitorId, range = 'weekly') {
    if (!monitorId) return;
    
    try {
        const res = await fetch(`${API_URL}/api/reports/monitor/${monitorId}?range=${range}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Failed to load report");
        
        const data = await res.json();
        
        document.getElementById('modal-report-title').innerText = `${data.monitor_name} Report`;
        document.getElementById('modal-uptime-val').innerText = `${data.uptime_percentage}%`;
        document.getElementById('modal-gauge-text').innerText = `${Math.round(data.uptime_percentage)}%`;
        
        const gauge = document.getElementById('modal-gauge');
        if (gauge) {
            gauge.style.setProperty('--gauge-percent', `${data.uptime_percentage}%`);
            
            // Color logic
            let color = '#ef4444';
            if (data.uptime_percentage >= 99.99) color = '#22c55e';
            else if (data.uptime_percentage >= 99.9) color = '#3b82f6';
            else if (data.uptime_percentage >= 99) color = '#eab308';
            
            gauge.style.setProperty('--gauge-color', color);
            document.getElementById('modal-uptime-val').style.color = color;
            
            const badge = document.getElementById('modal-sla-badge');
            if (badge) {
                badge.innerText = `Tier: ${data.sla_tier}`;
                badge.style.background = color + '1A';
                badge.style.color = color;
                badge.style.borderColor = color + '33';
            }
        }
        
        document.getElementById('modal-avg-resp').innerText = `${data.avg_response_time}ms`;
        document.getElementById('modal-total-inc').innerText = data.total_incidents;
        
        const downtimeEl = document.getElementById('modal-downtime');
        if (downtimeEl) downtimeEl.innerText = `${data.total_downtime_minutes}m`;
        
        const checksEl = document.getElementById('modal-total-checks');
        if (checksEl) checksEl.innerText = data.total_checks.toLocaleString();
        
        const descEl = document.getElementById('modal-period-desc');
        if (descEl) {
            const daysMap = { 'daily': '24 hours', 'weekly': '7 days', 'monthly': '30 days', 'yearly': '365 days' };
            descEl.innerText = `${data.total_checks.toLocaleString()} checks performed in last ${daysMap[range]}`;
        }
        
        lucide.createIcons();
    } catch (err) {
        console.error(err);
        showError("Failed to fetch monitor report.");
    }
}

async function openMonitorReport() {
    const monitorId = getMonitorId();
    const modal = document.getElementById('monitor-report-modal');
    if (modal) {
        modal.classList.add('active');
        const rangeSelector = document.getElementById('report-range');
        if (rangeSelector) {
            rangeSelector.value = 'weekly'; // Reset to default
        }
        await loadMonitorReport(monitorId, 'weekly');
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
    window.togglePause = togglePause;
    window.openMonitorReport = openMonitorReport;
    window.closeMonitorReport = closeMonitorReport;

    // Init
    document.addEventListener('DOMContentLoaded', () => {
        loadMonitorData();
        // Auto-refresh every 60 seconds
        setInterval(loadMonitorData, 60000);
        
        const rangeSelector = document.getElementById('report-range');
        if (rangeSelector) {
            rangeSelector.addEventListener('change', function() {
                loadMonitorReport(getMonitorId(), this.value);
            });
        }
    });

    async function initUserMap() {
        const mapContainer = document.getElementById('user-map');
        if (!mapContainer) return;

        let geoData = {
            country_code: 'US',
            country_name: 'United States',
            city: 'New York',
            latitude: 40.7128,
            longitude: -74.0060
        };

        try {
            // 1. Fetch Location (with timeout)
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);
            
            const geoRes = await fetch('https://ipapi.co/json/', { signal: controller.signal });
            clearTimeout(timeoutId);
            
            if (geoRes.ok) {
                geoData = await geoRes.json();
            }
        } catch (err) {
            console.warn("Map geo-location failed, using default fallback", err);
        }
            
        const { country_code, country_name, city, latitude, longitude } = geoData;
        
        // 2. Update Text
        const accessTextEl = document.getElementById('user-access-text');
        if (accessTextEl) {
            accessTextEl.innerText = `Accessed from ${city || 'Global Layer'}, ${country_name || 'Monitoring Node'}`;
        }

        // 3. Init Map
        if (window.jsVectorMap) {
            try {
                userMapInstance = new jsVectorMap({
                    selector: '#user-map',
                    map: 'world',
                    backgroundColor: 'transparent',
                    draggable: true,
                    zoomButtons: false,
                    regionsSelectable: false,
                    markerStyle: {
                        initial: { fill: '#3b82f6', stroke: '#fff', strokeWidth: 2, r: 5 },
                        hover: { fill: '#2563eb' }
                    },
                    regionStyle: {
                        initial: { fill: 'rgba(255,255,255,0.08)', stroke: 'rgba(255,255,255,0.05)', strokeWidth: 0.5 },
                        hover: { fill: 'rgba(59, 130, 246, 0.2)' }
                    },
                    selectedRegions: country_code ? [country_code] : [],
                    selectedRegionStyle: {
                        initial: { fill: 'rgba(59, 130, 246, 0.3)' }
                    },
                    markers: [
                        { name: city || 'Access Point', coords: [latitude || 0, longitude || 0] }
                    ]
                });
            } catch(e) { console.error("jsVectorMap init error:", e); }
        } else {
            console.error("jsVectorMap library not found");
        }
    }

    // Exposure to global scope
    window.loadMonitorReport = loadMonitorReport;

})();
