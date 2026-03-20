/**
 * app.js – License Admin SPA
 */

const Admin = {
    token: localStorage.getItem('admin_token') || null,
    licenses: [],
    filteredLicenses: [],

    // ── Bootstrap ─────────────────────────────────────────────
    async init() {
        this._bindLogin();
        this._bindUI();

        if (this.token) {
            await this._tryAutoLogin();
        }
    },

    async _tryAutoLogin() {
        try {
            const res = await this._req('GET', '/api/stats');
            if (res.total !== undefined) {
                this._showApp();
                await this.loadAll();
            }
        } catch {
            this._clearToken();
        }
    },

    // ── Auth ──────────────────────────────────────────────────
    _bindLogin() {
        document.getElementById('login-btn').addEventListener('click', () => this._doLogin());
        document.getElementById('admin-password').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this._doLogin();
        });
    },

    async _doLogin() {
        const pw = document.getElementById('admin-password').value;
        const errEl = document.getElementById('login-error');
        errEl.classList.add('hidden');

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: pw }),
            });
            if (!res.ok) throw new Error('Contraseña incorrecta');
            const data = await res.json();
            this.token = data.token;
            localStorage.setItem('admin_token', this.token);
            this._showApp();
            await this.loadAll();
        } catch (err) {
            errEl.textContent = err.message;
            errEl.classList.remove('hidden');
        }
    },

    _clearToken() {
        this.token = null;
        localStorage.removeItem('admin_token');
    },

    _showApp() {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
    },

    _showLogin() {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('main-app').classList.add('hidden');
    },

    // ── UI bindings ───────────────────────────────────────────
    _bindUI() {
        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            this._clearToken();
            this._showLogin();
        });

        // New license
        document.getElementById('new-license-btn').addEventListener('click', () => {
            this._openModal();
        });

        // Modal close
        document.getElementById('modal-close').addEventListener('click', () => this._closeModal());
        document.getElementById('modal-cancel').addEventListener('click', () => this._closeModal());
        document.getElementById('key-modal-close').addEventListener('click', () => {
            document.getElementById('key-modal').classList.add('hidden');
        });

        // Close modal on overlay click
        document.getElementById('license-modal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this._closeModal();
        });
        document.getElementById('key-modal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) document.getElementById('key-modal').classList.add('hidden');
        });

        // Form submit
        document.getElementById('license-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this._submitForm();
        });

        // Copy key
        document.getElementById('copy-key-btn').addEventListener('click', () => {
            const key = document.getElementById('key-modal-value').textContent;
            navigator.clipboard.writeText(key).then(() => this._toast('Clave copiada', 'success'));
        });

        // Search
        document.getElementById('search-input').addEventListener('input', (e) => {
            this._filterTable(e.target.value);
        });
    },

    // ── Data loading ──────────────────────────────────────────
    async loadAll() {
        await Promise.all([this._loadStats(), this._loadLicenses()]);
    },

    async _loadStats() {
        try {
            const s = await this._req('GET', '/api/stats');
            document.getElementById('stat-total').textContent   = s.total;
            document.getElementById('stat-active').textContent  = s.active;
            document.getElementById('stat-revoked').textContent = s.revoked;
            document.getElementById('stat-expired').textContent = s.expired;
        } catch { /* silent */ }
    },

    async _loadLicenses() {
        document.getElementById('licenses-loading').classList.remove('hidden');
        document.getElementById('licenses-table').classList.add('hidden');
        document.getElementById('no-results').classList.add('hidden');

        try {
            const data = await this._req('GET', '/api/licenses');
            this.licenses = data.licenses;
            this._filterTable(document.getElementById('search-input').value);
            document.getElementById('licenses-loading').classList.add('hidden');
        } catch (err) {
            document.getElementById('licenses-loading').textContent = `Error: ${err.message}`;
        }
    },

    _filterTable(query) {
        const q = query.toLowerCase();
        this.filteredLicenses = q
            ? this.licenses.filter(l =>
                l.client_name.toLowerCase().includes(q) ||
                l.client_email.toLowerCase().includes(q) ||
                l.key.toLowerCase().includes(q)
              )
            : this.licenses;

        this._renderTable();
    },

    _renderTable() {
        const tbody = document.getElementById('licenses-tbody');
        const table = document.getElementById('licenses-table');
        const noRes = document.getElementById('no-results');

        if (!this.filteredLicenses.length) {
            table.classList.add('hidden');
            noRes.classList.remove('hidden');
            return;
        }

        table.classList.remove('hidden');
        noRes.classList.add('hidden');

        tbody.innerHTML = this.filteredLicenses.map(l => {
            const status = l.computed_status || l.status;
            const badgeClass = { active: 'badge-active', revoked: 'badge-revoked', expired: 'badge-expired' }[status] || 'badge-active';
            const badgeLabel = { active: '✅ Activa', revoked: '🚫 Revocada', expired: '⏰ Vencida' }[status] || status;
            const expiry = l.expires_at ? new Date(l.expires_at).toLocaleDateString('es-AR') : '∞ Sin vencimiento';
            const lastSeen = l.last_seen ? this._relativeTime(l.last_seen) : 'Nunca';
            const keyShort = l.key.substring(0, 8) + '…' + l.key.substring(l.key.length - 4);

            return `<tr>
                <td>${l.id}</td>
                <td>
                    <div class="client-name">${this._esc(l.client_name)}</div>
                    <div class="client-email">${this._esc(l.client_email || '')}</div>
                </td>
                <td>${this._esc(l.client_email || '—')}</td>
                <td>
                    <span class="key-cell" title="${l.key}">${keyShort}</span>
                </td>
                <td>${expiry}</td>
                <td><span class="badge ${badgeClass}">${badgeLabel}</span></td>
                <td>${lastSeen}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-outline btn-sm" onclick="Admin._showKey(${l.id})">🔑</button>
                        <button class="btn btn-outline btn-sm" onclick="Admin._openModal(${l.id})">✏️</button>
                        ${status === 'active'
                            ? `<button class="btn btn-danger btn-sm" onclick="Admin._revoke(${l.id})">🚫</button>`
                            : `<button class="btn btn-success btn-sm" onclick="Admin._restore(${l.id})">✅</button>`
                        }
                        <button class="btn btn-danger btn-sm" onclick="Admin._delete(${l.id})">🗑️</button>
                    </div>
                </td>
            </tr>`;
        }).join('');
    },

    // ── Actions ───────────────────────────────────────────────
    _showKey(id) {
        const lic = this.licenses.find(l => l.id === id);
        if (!lic) return;
        document.getElementById('key-modal-client').textContent = `Cliente: ${lic.client_name}`;
        document.getElementById('key-modal-value').textContent = lic.key;
        document.getElementById('key-modal').classList.remove('hidden');
    },

    async _revoke(id) {
        if (!confirm('¿Revocar esta licencia? El cliente perderá el acceso de inmediato.')) return;
        try {
            await this._req('POST', `/api/licenses/${id}/revoke`);
            this._toast('Licencia revocada', 'success');
            await this.loadAll();
        } catch (err) {
            this._toast(`Error: ${err.message}`, 'error');
        }
    },

    async _restore(id) {
        try {
            await this._req('POST', `/api/licenses/${id}/restore`);
            this._toast('Licencia reactivada', 'success');
            await this.loadAll();
        } catch (err) {
            this._toast(`Error: ${err.message}`, 'error');
        }
    },

    async _delete(id) {
        const lic = this.licenses.find(l => l.id === id);
        if (!confirm(`¿Eliminar permanentemente la licencia de "${lic?.client_name}"? Esta acción no se puede deshacer.`)) return;
        try {
            await this._req('DELETE', `/api/licenses/${id}`);
            this._toast('Licencia eliminada', 'success');
            await this.loadAll();
        } catch (err) {
            this._toast(`Error: ${err.message}`, 'error');
        }
    },

    // ── Modal ─────────────────────────────────────────────────
    _openModal(id = null) {
        const form = document.getElementById('license-form');
        form.reset();
        document.getElementById('modal-license-id').value = '';

        if (id) {
            const lic = this.licenses.find(l => l.id === id);
            if (lic) {
                document.getElementById('modal-title').textContent = 'Editar Licencia';
                document.getElementById('modal-submit').textContent = 'Guardar cambios';
                document.getElementById('modal-license-id').value = id;
                document.getElementById('modal-client-name').value = lic.client_name;
                document.getElementById('modal-client-email').value = lic.client_email || '';
                document.getElementById('modal-expires').value = lic.expires_at ? lic.expires_at.substring(0, 10) : '';
                document.getElementById('modal-notes').value = lic.notes || '';
            }
        } else {
            document.getElementById('modal-title').textContent = 'Nueva Licencia';
            document.getElementById('modal-submit').textContent = 'Crear Licencia';
        }

        document.getElementById('license-modal').classList.remove('hidden');
    },

    _closeModal() {
        document.getElementById('license-modal').classList.add('hidden');
    },

    async _submitForm() {
        const id = document.getElementById('modal-license-id').value;
        const payload = {
            client_name:  document.getElementById('modal-client-name').value.trim(),
            client_email: document.getElementById('modal-client-email').value.trim(),
            notes:        document.getElementById('modal-notes').value.trim(),
            expires_at:   document.getElementById('modal-expires').value || null,
        };

        const btn = document.getElementById('modal-submit');
        btn.disabled = true;
        btn.textContent = 'Guardando…';

        try {
            if (id) {
                await this._req('PUT', `/api/licenses/${id}`, payload);
                this._toast('Licencia actualizada', 'success');
            } else {
                const created = await this._req('POST', '/api/licenses', payload);
                this._toast('Licencia creada', 'success');
                this._closeModal();
                await this.loadAll();
                // Auto-show new key
                setTimeout(() => this._showKey(created.id), 300);
                return;
            }
            this._closeModal();
            await this.loadAll();
        } catch (err) {
            this._toast(`Error: ${err.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = id ? 'Guardar cambios' : 'Crear Licencia';
        }
    },

    // ── Helpers ───────────────────────────────────────────────
    async _req(method, path, body) {
        const opts = {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
            },
        };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(path, opts);
        if (res.status === 401) {
            this._clearToken();
            this._showLogin();
            throw new Error('Sesión expirada');
        }
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return res.json();
    },

    _toast(msg, type = 'info') {
        const c = document.getElementById('toast-container');
        const t = document.createElement('div');
        t.className = `toast toast-${type}`;
        t.textContent = msg;
        c.appendChild(t);
        setTimeout(() => t.remove(), 4000);
    },

    _esc(str) {
        return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    },

    _relativeTime(iso) {
        const diff = Date.now() - new Date(iso).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1)  return 'Ahora mismo';
        if (mins < 60) return `hace ${mins}m`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24)  return `hace ${hrs}h`;
        const days = Math.floor(hrs / 24);
        return `hace ${days}d`;
    },
};

document.addEventListener('DOMContentLoaded', () => Admin.init());
