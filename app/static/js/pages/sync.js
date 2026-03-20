/**
 * pages/sync.js – Sync page controller.
 */
const SyncPage = {
    _pollTimer: null,

    async init() {
        document.getElementById('run-sync-btn').addEventListener('click', () => this.runSync());
        await this.loadHistory();
    },

    async runSync() {
        const btn = document.getElementById('run-sync-btn');
        btn.disabled = true;
        btn.textContent = '⏳ Ejecutando…';

        const progress = document.getElementById('sync-progress');
        const progressText = document.getElementById('sync-progress-text');
        const statusDiv = document.getElementById('sync-current-status');
        progress.classList.remove('hidden');
        progressText.textContent = 'Obteniendo propiedades de Tokko Broker…';

        try {
            const res = await API.runSync();
            if (res.sync_id === 0) {
                App.toast('Ya hay un sync en ejecución', 'info');
                btn.disabled = false;
                btn.textContent = '▶️ Ejecutar Sync';
                progress.classList.add('hidden');
                return;
            }

            App.toast('Sync iniciado', 'info');

            // Poll status
            this._pollTimer = setInterval(async () => {
                try {
                    const status = await API.getSyncStatus();
                    if (!status.running) {
                        clearInterval(this._pollTimer);
                        this._pollTimer = null;

                        const fill = document.getElementById('sync-progress-fill');
                        fill.style.width = '100%';
                        fill.style.animation = 'none';
                        progressText.textContent = '✅ Sync completado';

                        btn.disabled = false;
                        btn.textContent = '▶️ Ejecutar Sync';

                        await this.loadHistory();
                        App.toast('Sync completado', 'success');
                    } else {
                        progressText.textContent = 'Procesando…';
                    }
                } catch (e) {
                    console.error('Poll error:', e);
                }
            }, 2000);

        } catch (err) {
            progress.classList.add('hidden');
            btn.disabled = false;
            btn.textContent = '▶️ Ejecutar Sync';
            App.toast(`Error: ${err.message}`, 'error');
        }
    },

    async loadHistory() {
        try {
            const data = await API.getSyncHistory();
            const list = document.getElementById('sync-history-list');
            const history = data.history || [];

            if (!history.length) {
                list.innerHTML = '<p class="muted">No hay syncs todavía</p>';
                return;
            }

            const rows = history.map(h => {
                const dt = h.started_at
                    ? new Date(h.started_at).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' })
                    : '—';
                const duration = h.finished_at && h.started_at
                    ? ((new Date(h.finished_at) - new Date(h.started_at)) / 1000).toFixed(1) + 's'
                    : '—';
                return `<tr>
                    <td>${dt}</td>
                    <td><span class="status-badge ${h.status}">${h.status}</span></td>
                    <td>${h.fetched || 0}</td>
                    <td>${h.mapped || 0}</td>
                    <td>${duration}</td>
                    <td>${h.upload_id || '—'}</td>
                    <td>${h.error ? `<span title="${h.error}" style="cursor:help">⚠️</span>` : '✓'}</td>
                </tr>`;
            }).join('');

            list.innerHTML = `
                <table>
                    <thead><tr>
                        <th>Fecha</th><th>Estado</th><th>Obtenidas</th>
                        <th>Mapeadas</th><th>Duración</th><th>Upload ID</th><th></th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table>
            `;
        } catch (err) {
            console.error('Load history failed:', err);
        }
    }
};
