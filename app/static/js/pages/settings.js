/**
 * pages/settings.js – Settings page controller.
 */
const SettingsPage = {
    async init() {
        await this.loadSettings();
        this.bindEvents();
    },

    async loadSettings() {
        try {
            const s = await API.getSettings();
            const form = document.getElementById('settings-form');
            for (const [key, val] of Object.entries(s)) {
                const el = form.querySelector(`[name="${key}"]`);
                if (!el) continue;
                // Don't overwrite textarea with masked value
                if (el.tagName === 'TEXTAREA' && val && val.startsWith('•')) {
                    el.placeholder = '(credenciales guardadas — pegá nuevo JSON para reemplazar)';
                } else {
                    el.value = val || '';
                }
            }
        } catch (err) {
            console.error('Failed to load settings:', err);
        }
    },

    bindEvents() {
        // Save form
        document.getElementById('settings-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const data = Object.fromEntries(new FormData(form));
            try {
                const res = await API.saveSettings(data);
                this._showResult('settings-save-result', true, `✅ ${res.message} (${res.count} campos)`);
                App.toast('Configuración guardada', 'success');
            } catch (err) {
                this._showResult('settings-save-result', false, `❌ Error: ${err.message}`);
            }
        });

        // Test Tokko
        document.getElementById('test-tokko-btn').addEventListener('click', async () => {
            await this._runTest('test-tokko-btn', 'test-tokko-result', () => API.testTokko(), '🧪 Test conexión');
        });

        // Test Meta
        document.getElementById('test-meta-btn').addEventListener('click', async () => {
            await this._runTest('test-meta-btn', 'test-meta-result', () => API.testMeta(), '🧪 Test conexión');
        });

        // Test GA4
        document.getElementById('test-ga4-btn').addEventListener('click', async () => {
            await this._runTest('test-ga4-btn', 'test-ga4-result', () => API.testGA4(), '🧪 Test GA4');
        });
    },

    async _runTest(btnId, resultId, apiFn, btnLabel) {
        const btn = document.getElementById(btnId);
        btn.disabled = true;
        btn.textContent = '⏳ Probando…';
        try {
            const res = await apiFn();
            this._showResult(resultId, res.success, res.message);
        } catch (err) {
            this._showResult(resultId, false, `Error: ${err.message}`);
        }
        btn.disabled = false;
        btn.textContent = btnLabel;
    },

    _showResult(id, success, msg) {
        const el = document.getElementById(id);
        el.textContent = msg;
        el.className = `test-result ${success ? 'success' : 'error'}`;
        el.classList.remove('hidden');
    }
};
