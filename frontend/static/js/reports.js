(function() {
    const API_URL = window.API_URL || window.location.origin;
    const token = window.token || localStorage.getItem('token');
    const REPORTS_API = API_URL + '/api/reports';

async function loadReports() {
    try {
        const [weekly, monthly, yearly, monitors] = await Promise.all([
            fetch(`${REPORTS_API}/weekly`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()),
            fetch(`${REPORTS_API}/monthly`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()),
            fetch(`${REPORTS_API}/yearly`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()),
            fetch(`${REPORTS_API}/monitors`, { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json())
        ]);

        // Populate Weekly
        updateGauge('weekly-uptime', weekly.uptime_percentage);
        document.getElementById('weekly-uptime-val').innerText = `${weekly.uptime_percentage}%`;
        updateSiteCounts(weekly.total_monitors);
        document.querySelector('.check-count').innerText = weekly.total_checks.toLocaleString();
        renderSparkline('weekly-sparkline', weekly.trends.uptime, '#10b981');
        
        const weeklyUptimeText = document.getElementById('weekly-uptime-text');
        if (weeklyUptimeText) weeklyUptimeText.innerHTML = `${Math.round(weekly.uptime_percentage)}%<br><small style="font-size:8px; opacity:0.6">${weekly.sla_tier}</small>`;

        // Populate Monthly
        updateGauge('monthly-uptime', monthly.uptime_percentage);
        document.getElementById('monthly-uptime-val').innerText = `${monthly.uptime_percentage}%`;
        document.querySelector('.monthly-check-count').innerText = monthly.total_checks.toLocaleString();
        renderSparkline('monthly-sparkline', monthly.trends.uptime, '#3b82f6');
        
        const monthlyUptimeText = document.getElementById('monthly-uptime-text');
        if (monthlyUptimeText) monthlyUptimeText.innerHTML = `${Math.round(monthly.uptime_percentage)}%<br><small style="font-size:8px; opacity:0.6">${monthly.sla_tier}</small>`;

        // Populate Response (from weekly data)
        document.getElementById('avg-response-text').innerText = `${Math.round(weekly.average_response_time)}ms`;
        document.getElementById('avg-response-val').innerText = `${Math.round(weekly.average_response_time)}ms`;
        updateResponseGauge(weekly.average_response_time);
        renderSparkline('response-trend-sparkline', weekly.trends.response_time, '#10b981');

        // Populate Yearly
        updateGauge('yearly-uptime', yearly.uptime_percentage);
        document.getElementById('yearly-uptime-val').innerText = `${yearly.uptime_percentage}%`;
        document.querySelector('.yearly-check-count').innerText = yearly.total_checks.toLocaleString();
        renderSparkline('yearly-sparkline', yearly.trends.uptime, '#3b82f6');
        
        const yearlyUptimeText = document.getElementById('yearly-uptime-text');
        if (yearlyUptimeText) yearlyUptimeText.innerHTML = `${Math.round(yearly.uptime_percentage)}%<br><small style="font-size:8px; opacity:0.6">${yearly.sla_tier}</small>`;

        // Populate Summary
        const summaryUptime = document.getElementById('summary-uptime');
        if (summaryUptime) summaryUptime.innerText = `${weekly.uptime_percentage}%`;
        const summaryResponse = document.getElementById('summary-response');
        if (summaryResponse) summaryResponse.innerText = `${Math.round(weekly.average_response_time)}ms`;
        const summaryDowntime = document.getElementById('summary-downtime');
        if (summaryDowntime) summaryDowntime.innerText = `${Math.round(yearly.total_downtime_minutes)} Minutes`;
        const summaryIncidents = document.getElementById('summary-incidents');
        if (summaryIncidents) summaryIncidents.innerText = `${yearly.total_incidents} Incidents`;
        
        renderSparkline('summary-uptime-spark', weekly.trends.uptime, '#10b981');
        renderSparkline('summary-response-spark', weekly.trends.response_time, '#3b82f6');
        const downtimeTrend = weekly.trends.uptime.map(v => 100 - v);
        renderSparkline('summary-downtime-spark', downtimeTrend, '#ef4444');
        renderSparkline('summary-incidents-spark', weekly.trends.incidents, '#f59e0b');

        // Populate Monitor List
        renderMonitorList(monitors);

        lucide.createIcons();

    } catch (err) {
        console.error("Failed to load reports:", err);
    }
}

function renderMonitorList(monitors) {
    const grid = document.getElementById('monitor-list-grid');
    if (!grid) return;

    if (!monitors || monitors.length === 0) {
        grid.innerHTML = '<div class="summary-card" style="grid-column: span 2; text-align:center; color:#4d6a80;">No active monitors found for reporting.</div>';
        return;
    }

    grid.innerHTML = monitors.map(mon => {
        let color = '#ef4444';
        if (mon.uptime_percentage >= 99.99) color = '#22c55e';
        else if (mon.uptime_percentage >= 99.9) color = '#3b82f6';
        else if (mon.uptime_percentage >= 99) color = '#eab308';

        return `
        <div class="summary-card" style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div class="summary-label" style="margin-bottom:8px; font-size:12px; color:#fff;">${mon.name}</div>
            <div style="display:flex; align-items:center; gap:10px;">
              <span class="sla-badge" style="background:${color}1A; color:${color}; border-color:${color}33;">Tier: ${mon.sla_tier}</span>
              <span style="font-size:13px; color:#4d6a80;">30D Uptime</span>
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:24px; font-weight:800; color:${color};">${mon.uptime_percentage}%</div>
            <a href="/monitors/${mon.id}" style="font-size:11px; color:#3b82f6; text-decoration:none;">View Details &rarr;</a>
          </div>
        </div>
        `;
    }).join('');
}

function updateGauge(id, percent) {
    const gauge = document.getElementById(`${id}-gauge`);
    if (!gauge) return;

    const offset = 314 - (percent / 100 * 314);
    gauge.style.strokeDasharray = `${314 - offset}, 314`;
    
    // Color logic
    if (percent >= 99.99) gauge.style.stroke = '#10b981';
    else if (percent >= 99.9) gauge.style.stroke = '#3b82f6';
    else if (percent >= 99) gauge.style.stroke = '#f59e0b';
    else gauge.style.stroke = '#ef4444';
}

function updateResponseGauge(avg) {
    const gauge = document.getElementById('response-performance-gauge');
    if (!gauge) return;
    const score = Math.max(0, Math.min(100, (1000 - avg) / 10));
    const offset = 314 - (score / 100 * 314);
    gauge.style.strokeDasharray = `${314 - offset}, 314`;
    gauge.style.stroke = avg < 300 ? '#10b981' : (avg < 800 ? '#3b82f6' : '#ef4444');
}

function updateSiteCounts(count) {
    document.querySelectorAll('.site-count').forEach(el => el.innerText = count);
}

function renderSparkline(canvasId, data, color) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const existingChart = Chart.getChart(canvasId);
    if (existingChart) existingChart.destroy();

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map((_, i) => i),
            datasets: [{
                data: data,
                borderColor: color,
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                backgroundColor: (context) => {
                    const chart = context.chart;
                    const {ctx, chartArea} = chart;
                    if (!chartArea) return null;
                    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                    gradient.addColorStop(0, 'rgba(0,0,0,0)');
                    gradient.addColorStop(1, color.replace(')', ', 0.15)').replace('rgb', 'rgba'));
                    return gradient;
                },
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: { x: { display: false }, y: { display: false } }
        }
    });
}

function downloadPDF() {
    const url = `${REPORTS_API}/export`;
    fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "MoniFy-Report.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(err => {
        console.error("PDF Export failed:", err);
    });
}

    // Exposure to global scope
    window.loadReports = loadReports;
    window.downloadPDF = downloadPDF;

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            if (window.location.pathname.includes('reports')) {
                loadReports();
            }
        });
    } else {
        if (window.location.pathname.includes('reports')) {
            loadReports();
        }
    }

})();
