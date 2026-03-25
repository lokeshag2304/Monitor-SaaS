(function() {
    const API_URL = window.API_URL || window.location.origin;
    const token = localStorage.getItem('token');
    
    let currentReportData = null;
    let uptimeChart = null;
    let responseChart = null;
    let selectedMonitorIds = [];

    // Main Init
    async function init() {
        console.log("Reports System: Initializing...");
        if (!token) {
            console.error("No token found, redirecting to login.");
            window.location.href = '/login';
            return;
        }

        try {
            await fetchMonitors();
            setupEventListeners();
            console.log("Reports loaded successfully.");
            
            // Auto generate initial report since empty state is removed
            setTimeout(() => generateReport(), 100); 
        } catch (err) {
            console.error("Reports load failed:", err);
            if (window.showError) showError("Failed to initialize reports");
        }
    }

    async function fetchMonitors() {
        try {
            const res = await fetch(`${API_URL}/api/reports/monitors`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Server responded with " + res.status);
            const monitors = await res.json();
            
            if (!Array.isArray(monitors)) {
                throw new Error("Expected array of monitors, got " + typeof monitors);
            }
            
            renderMonitorChecklist(monitors);
        } catch (err) {
            console.error('Failed to fetch monitors:', err);
            const container = document.getElementById('monitor-checkboxes');
            if (container) container.innerHTML = `<div class="text-red-500 text-xs p-4">Error: ${err.message}</div>`;
        }
    }

    function renderMonitorChecklist(monitors) {
        const container = document.getElementById('monitor-checkboxes');
        if (!container) return;

        let html = `
            <label class="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer border-b border-white/5 mb-2 pb-3">
                <input type="checkbox" id="check-all-monitors" checked class="w-4 h-4 rounded border-white/10 bg-white/5 text-primary focus:ring-primary">
                <span class="text-sm font-bold text-white">Select All Systems</span>
            </label>
            <div class="space-y-1">
        `;

        html += monitors.map(m => `
            <label class="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors">
                <input type="checkbox" class="mon-cb w-4 h-4 rounded border-white/10 bg-white/5 text-primary focus:ring-primary" value="${m.id}" data-name="${m.name || m.url}" checked>
                <div class="flex flex-col">
                    <span class="text-xs font-bold text-gray-200">${m.name || m.url}</span>
                    <span class="text-[9px] text-gray-500 uppercase font-bold tracking-tighter">${m.url}</span>
                </div>
            </label>
        `).join('');

        html += `</div>`;

        container.innerHTML = html;
        updateSelectedText();

        const checkAll = document.getElementById('check-all-monitors');
        const cbs = document.querySelectorAll('.mon-cb');

        if (checkAll) {
            checkAll.addEventListener('change', () => {
                cbs.forEach(cb => cb.checked = checkAll.checked);
                updateSelectedText();
            });
        }

        cbs.forEach(cb => {
            cb.addEventListener('change', () => {
                if (checkAll) checkAll.checked = Array.from(cbs).every(c => c.checked);
                updateSelectedText();
            });
        });
    }

    function updateSelectedText() {
        const cbs = document.querySelectorAll('.mon-cb:checked');
        const text = document.getElementById('selected-monitors-text');
        if (!text) return;

        if (cbs.length === 0) text.innerText = 'Select Systems';
        else if (cbs.length === document.querySelectorAll('.mon-cb').length) text.innerText = 'All Global Systems';
        else text.innerText = `${cbs.length} Systems Selected`;
        
        selectedMonitorIds = Array.from(cbs).map(cb => cb.value);
    }

    function setupEventListeners() {
        const trigger = document.getElementById('monitor-select-trigger');
        const dropdown = document.getElementById('monitor-dropdown');
        
        if (trigger && dropdown) {
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.toggle('hidden');
                // Optional: add a slight animation or focus effect
            });
            
            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target) && !trigger.contains(e.target)) {
                    dropdown.classList.add('hidden');
                }
            });
        }

        const genBtn = document.getElementById('generate-btn');
        if (genBtn) genBtn.addEventListener('click', generateReport);
        
        const customBtn = document.getElementById('custom-range-btn');
        if (customBtn) {
            customBtn.addEventListener('click', () => {
                const modal = document.getElementById('custom-modal');
                if (modal) modal.style.display = 'flex';
            });
        }

        const applyBtn = document.getElementById('apply-custom-range');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                const modal = document.getElementById('custom-modal');
                if (modal) modal.style.display = 'none';
                generateReport();
            });
        }
    }

    async function generateReport() {
        if (selectedMonitorIds.length === 0) {
            if (window.showError) showError('Please select at least one monitor');
            else alert('Please select at least one monitor');
            return;
        }

        const btn = document.getElementById('generate-btn');
        const originalContent = btn.innerHTML;
        btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Processing...`;
        if (window.lucide) lucide.createIcons();
        btn.disabled = true;

        const days = document.getElementById('time-range-select').value;
        const ids = selectedMonitorIds.join(',');

        try {
            const res = await fetch(`${API_URL}/api/reports/dynamic?ids=${ids}&days=${days}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Failed to fetch report data");
            const data = await res.json();
            currentReportData = data;
            showReportContent(data);
            if (window.showSuccess) showSuccess("Audit computed successfully!");
        } catch (err) {
            console.error('Report failed:', err);
            if (window.showError) showError("System audit failed to generate");
        } finally {
            btn.innerHTML = originalContent;
            btn.disabled = false;
            if (window.lucide) lucide.createIcons();
        }
    }

    function showReportContent(data) {
        const emptyState = document.getElementById('report-empty');
        const contentArea = document.getElementById('report-content');
        
        if (emptyState) emptyState.classList.add('hidden');
        if (contentArea) contentArea.classList.remove('hidden');
        
        // Stats
        safeSet('val-uptime', `${data.uptime_percentage}%`);
        safeSet('val-response', `${data.average_response_time}ms`);
        safeSet('val-checks', data.total_checks.toLocaleString());
        
        const dm = data.total_downtime_minutes;
        const formattedDowntime = dm > 60 ? `${Math.floor(dm/60)}h ${Math.floor(dm%60)}m` : `${Math.floor(dm)}m ${Math.round((dm%1)*60)}s`;
        safeSet('val-downtime', formattedDowntime);

        // Diffs
        updateDiff('diff-uptime', data.diffs.uptime, '%', true);
        updateDiff('diff-response', data.diffs.response, 'ms', false); // lower is better
        updateDiff('diff-checks', data.diffs.checks, '', true);
        updateDiff('diff-downtime', data.diffs.downtime, 'm', false);

        // Chart Labels
        const days = document.getElementById('time-range-select').value;
        safeSet('chart-period-uptime', `LAST ${days} DAYS`);

        renderCharts(data.trends);
        renderPerformanceTable(data.monitors_performance);
        renderIncidents(data.latest_incidents);
        if (window.lucide) lucide.createIcons();
    }

    function safeSet(id, val) {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
    }

    function updateDiff(id, val, unit, higherBetter) {
        const el = document.getElementById(id);
        if (!el) return;
        
        const isUp = val >= 0;
        const colorClass = (isUp === higherBetter) ? 'text-green-500' : 'text-red-500';
        const icon = isUp ? 'arrow-up-right' : 'arrow-down-right';
        
        el.className = `text-[11px] font-bold flex items-center gap-1 ${colorClass}`;
        el.innerHTML = `<i data-lucide="${icon}" class="w-3 h-3"></i> ${Math.abs(val)}${unit}`;
    }

    function renderCharts(trends) {
        if (!window.Chart) return;

        if (uptimeChart) uptimeChart.destroy();
        if (responseChart) responseChart.destroy();

        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
            scales: {
                x: { display: false },
                y: { display: true, grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false }, ticks: { color: '#64748b', font: { size: 10 } } }
            }
        };

        const upCtx = document.getElementById('uptime-chart');
        if (upCtx) {
            uptimeChart = new Chart(upCtx, {
                type: 'line',
                data: {
                    labels: trends.dates,
                    datasets: [{
                        label: 'Uptime',
                        data: trends.uptime,
                        borderColor: '#22c55e',
                        backgroundColor: (context) => {
                            const chart = context.chart;
                            const {ctx, chartArea} = chart;
                            if (!chartArea) return null;
                            const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                            gradient.addColorStop(0, 'rgba(34,197,94,0)');
                            gradient.addColorStop(1, 'rgba(34,197,94,0.15)');
                            return gradient;
                        },
                        fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2
                    }]
                },
                options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, min: 0, max: 100 } } }
            });
        }

        const resCtx = document.getElementById('response-chart');
        if (resCtx) {
            responseChart = new Chart(resCtx, {
                type: 'line',
                data: {
                    labels: trends.dates,
                    datasets: [{
                        label: 'Latency',
                        data: trends.response_time,
                        borderColor: '#3b82f6',
                        backgroundColor: (context) => {
                            const chart = context.chart;
                            const {ctx, chartArea} = chart;
                            if (!chartArea) return null;
                            const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                            gradient.addColorStop(0, 'rgba(59,130,246,0)');
                            gradient.addColorStop(1, 'rgba(59,130,246,0.15)');
                            return gradient;
                        },
                        fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2
                    }]
                },
                options: commonOptions
            });
        }
    }

    function renderPerformanceTable(monitors) {
        const tbody = document.getElementById('performance-body');
        if (!tbody) return;

        tbody.innerHTML = monitors.map(m => `
            <tr class="hover:bg-white/[0.01] transition-colors">
                <td class="px-6 py-4">
                    <div class="flex flex-col">
                        <span class="text-sm font-bold text-white">${m.name}</span>
                        <span class="text-[10px] text-gray-600 font-bold uppercase tracking-widest">${m.checks} CHECKS</span>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <span class="text-[9px] font-black px-2 py-1 rounded-md border ${m.status.toLowerCase() === 'up' ? 'text-green-500 bg-green-500/10 border-green-500/20' : 'text-red-500 bg-red-500/10 border-red-500/20'} uppercase tracking-widest">
                        ${m.status}
                    </span>
                </td>
                <td class="px-6 py-4 text-center text-sm font-bold text-white font-mono">${m.uptime_percentage}%</td>
                <td class="px-6 py-4 text-center text-sm font-medium text-gray-400 font-mono">${m.avg_response_time}ms</td>
                <td class="px-6 py-4 text-center">
                    <div class="h-8 w-24 mx-auto">
                        <canvas id="spark-${m.id}"></canvas>
                    </div>
                </td>
            </tr>
        `).join('');

        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: { x: { display: false }, y: { display: false } }
        };

        monitors.forEach(m => {
            const ctx = document.getElementById(`spark-${m.id}`);
            if (ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: m.trend.map((_, i) => i),
                        datasets: [{ 
                            data: m.trend, 
                            borderColor: m.status.toLowerCase() === 'up' ? '#22c55e' : '#ef4444', 
                            borderWidth: 1.5, fill: false, pointRadius: 0, tension: 0.4 
                        }]
                    },
                    options: chartOptions
                });
            }
        });
    }

    function renderIncidents(incidents) {
        const list = document.getElementById('incidents-list');
        if (!list) return;

        if (incidents.length === 0) {
            list.innerHTML = `
                <div class="py-12 flex flex-col items-center justify-center text-center">
                    <div class="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
                        <i data-lucide="shield-check" class="text-gray-700 w-6 h-6"></i>
                    </div>
                    <p class="text-[10px] text-gray-500 font-bold uppercase tracking-widest">System Stable</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        list.innerHTML = incidents.map(i => `
            <div class="p-4 rounded-2xl bg-white/5 border border-white/5 flex items-center gap-4 group hover:border-white/10 transition-all">
                <div class="w-10 h-10 rounded-xl flex items-center justify-center ${i.resolved_at ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}">
                    <i data-lucide="${i.resolved_at ? 'check-circle' : 'alert-circle'}" class="w-5 h-5"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="text-xs font-bold text-white truncate">${i.monitor_name}</div>
                    <div class="flex items-center gap-2 mt-1">
                        <span class="text-[9px] font-black uppercase tracking-tighter ${i.resolved_at ? 'text-green-600' : 'text-red-600'}">${i.resolved_at ? 'Resolved' : 'Critical'}</span>
                        <span class="text-gray-700 font-bold text-[9px]">•</span>
                        <span class="text-[9px] text-gray-500 font-bold">${Math.round(i.duration_seconds/60)}m duration</span>
                    </div>
                </div>
                <div class="text-[9px] text-gray-700 font-bold uppercase tracking-tighter group-hover:text-gray-500 transition-colors">
                    ${new Date(i.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
            </div>
        `).join('');
    }

    async function downloadReport(format) {
        if (selectedMonitorIds.length === 0) {
            if (window.showError) showError('Select monitors to export');
            return;
        }

        const days = document.getElementById('time-range-select').value;
        const ids = selectedMonitorIds.join(',');
        const endpoint = format === 'csv' ? 'export/csv' : 'export';
        const url = `${API_URL}/api/reports/${endpoint}?ids=${ids}&days=${days}`;

        if (window.showInfo) showInfo(`Preparing ${format.toUpperCase()} report...`);

        try {
            const res = await fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }

            if (!res.ok) throw new Error('Export failed');

            const blob = await res.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = `MoniFy_Audit_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            if (window.showSuccess) showSuccess("Report downloaded!");
        } catch (err) {
            console.error('Export error:', err);
            if (window.showError) showError('Failed to export report');
        }
    }

    window.reports = {
        exportPDF: () => downloadReport('pdf'),
        exportCSV: () => downloadReport('csv')
    };

    document.addEventListener('DOMContentLoaded', init);
})();
