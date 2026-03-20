/**
 * analytics.js – Google Analytics 4 dashboard page.
 */
const AnalyticsPage = {
    currentDays: 30,
    data: null,

    async init() {
        this._bindPeriodSelector();
        await this.load(this.currentDays);
    },

    _bindPeriodSelector() {
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentDays = parseInt(btn.dataset.days);
                await this.load(this.currentDays);
            });
        });
    },

    async load(days) {
        this._setLoading(true);
        try {
            const data = await API.getAnalytics(days);
            this.data = data;
            this._render(data);
        } catch (err) {
            this._showError(`Error cargando analytics: ${err.message}`);
        } finally {
            this._setLoading(false);
        }
    },

    _setLoading(loading) {
        const el = document.getElementById('analytics-loading');
        if (el) el.classList.toggle('hidden', !loading);
        const content = document.getElementById('analytics-content');
        if (content) content.classList.toggle('hidden', loading);
    },

    _showError(msg) {
        const el = document.getElementById('analytics-error');
        if (!el) return;
        el.textContent = msg;
        el.classList.remove('hidden');
        const content = document.getElementById('analytics-content');
        if (content) content.classList.add('hidden');
    },

    _render(data) {
        const errEl = document.getElementById('analytics-error');
        if (errEl) errEl.classList.add('hidden');

        if (!data.configured) {
            this._showNotConfigured(data.error);
            return;
        }

        if (data.error) {
            this._showError(data.error);
            return;
        }

        this._renderKPIs(data.kpi);
        this._renderChart(data.daily);
        this._renderTopPages(data.top_pages);
        this._renderDevices(data.devices);

        const content = document.getElementById('analytics-content');
        if (content) content.classList.remove('hidden');
    },

    _showNotConfigured(msg) {
        const el = document.getElementById('analytics-not-configured');
        if (el) {
            el.classList.remove('hidden');
            const txt = el.querySelector('.not-configured-msg');
            if (txt) txt.textContent = msg || 'GA4 no configurado';
        }
        const content = document.getElementById('analytics-content');
        if (content) content.classList.add('hidden');
    },

    _renderKPIs(kpi) {
        const fmt = n => n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
        const fmtDur = s => {
            const m = Math.floor(s / 60);
            const sec = Math.round(s % 60);
            return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
        };

        this._setText('ga-sessions',   fmt(kpi.sessions));
        this._setText('ga-users',      fmt(kpi.users));
        this._setText('ga-pageviews',  fmt(kpi.pageviews));
        this._setText('ga-duration',   fmtDur(kpi.avg_session_duration));
        this._setText('ga-bounce',     `${kpi.bounce_rate}%`);
    },

    _renderChart(daily) {
        const container = document.getElementById('ga-chart');
        if (!container || !daily.length) return;

        const maxSessions = Math.max(...daily.map(d => d.sessions), 1);
        const bars = daily.map(d => {
            const heightPct = Math.max((d.sessions / maxSessions) * 100, 2);
            const label = d.date.slice(5); // "MM-DD"
            return `
                <div class="chart-bar-wrap" title="${d.date}: ${d.sessions} sesiones / ${d.users} usuarios">
                    <div class="chart-bar" style="height:${heightPct}%"></div>
                    <span class="chart-label">${label}</span>
                </div>`;
        }).join('');

        container.innerHTML = `<div class="chart-bars">${bars}</div>`;
    },

    _renderTopPages(pages) {
        const tbody = document.getElementById('ga-pages-body');
        if (!tbody) return;

        if (!pages.length) {
            tbody.innerHTML = '<tr><td colspan="3" class="muted">Sin datos</td></tr>';
            return;
        }

        const maxViews = pages[0].views || 1;
        tbody.innerHTML = pages.map((p, i) => `
            <tr>
                <td><span class="rank">${i + 1}</span></td>
                <td class="page-path" title="${p.page}">${p.page}</td>
                <td>
                    <div class="bar-cell">
                        <div class="bar-fill" style="width:${(p.views/maxViews*100).toFixed(0)}%"></div>
                        <span>${p.views.toLocaleString()}</span>
                    </div>
                </td>
                <td>${p.users.toLocaleString()}</td>
            </tr>`
        ).join('');
    },

    _renderDevices(devices) {
        const container = document.getElementById('ga-devices');
        if (!container) return;

        const icons = { desktop: '🖥️', mobile: '📱', tablet: '📟' };
        const colors = { desktop: 'var(--accent)', mobile: 'var(--accent-2)', tablet: 'var(--success)' };

        container.innerHTML = devices.map(d => `
            <div class="device-row">
                <div class="device-label">
                    <span>${icons[d.device] || '💻'}</span>
                    <span>${d.device}</span>
                </div>
                <div class="device-bar-wrap">
                    <div class="device-bar" style="width:${d.percentage}%; background:${colors[d.device] || 'var(--accent)'}"></div>
                </div>
                <div class="device-stats">
                    <span class="device-pct">${d.percentage}%</span>
                    <span class="device-count">${d.sessions.toLocaleString()} ses.</span>
                </div>
            </div>`
        ).join('');
    },

    _setText(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    },
};
