/**
 * pages/dashboard.js – Dashboard page controller.
 */
const DashboardPage = {
    async init() {
        await this.loadStats();
    },

    async loadStats() {
        try {
            const data = await API.getSyncHistory();
            const history = data.history || [];

            // Latest sync
            const latest = history[0];
            if (latest) {
                document.getElementById('stat-tokko-val').textContent = latest.fetched || '—';
                document.getElementById('stat-synced-val').textContent = latest.mapped || '—';
                document.getElementById('stat-skipped-val').textContent = latest.skipped || '—';
                const dt = latest.finished_at || latest.started_at;
                document.getElementById('stat-last-val').textContent = dt
                    ? new Date(dt).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' })
                    : '—';
            }

            // History table
            this.renderHistory(history);
        } catch (err) {
            console.error('Dashboard load failed:', err);
        }
    },

    renderHistory(history) {
        const container = document.getElementById('dashboard-history');
        if (!history.length) {
            container.innerHTML = '<p class="muted">No hay syncs todavía</p>';
            return;
        }

        const rows = history.map(h => {
            const dt = h.started_at ? new Date(h.started_at).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' }) : '—';
            return `<tr>
                <td>${dt}</td>
                <td><span class="status-badge ${h.status}">${h.status}</span></td>
                <td>${h.fetched || 0}</td>
                <td>${h.mapped || 0}</td>
                <td>${h.skipped || 0}</td>
                <td>${h.error ? `<span title="${h.error}">⚠️</span>` : '—'}</td>
            </tr>`;
        }).join('');

        container.innerHTML = `
            <table>
                <thead><tr>
                    <th>Fecha</th><th>Estado</th><th>Obtenidas</th>
                    <th>Mapeadas</th><th>Omitidas</th><th>Error</th>
                </tr></thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    }
};
