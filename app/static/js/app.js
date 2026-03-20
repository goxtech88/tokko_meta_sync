/**
 * app.js – SPA router, license gate, and global utilities.
 */
const App = {
    currentPage: 'dashboard',

    async init() {
        // ── License gate (desactivado temporalmente) ──────────
        // Para reactivar: descomentar las 3 líneas de abajo y borrar el this.showApp({})
        // const lic = await API.getLicenseStatus();
        // if (!lic.active) { this.showLicenseGate(); return; }
        // this.showApp(lic);
        this.showApp({});
        // ─────────────────────────────────────────────────────

        this.bindNav();
        this.navigateTo('dashboard');
    },

    showLicenseGate() {
        document.getElementById('license-gate').classList.remove('hidden');
        document.getElementById('app').classList.add('hidden');

        document.getElementById('license-activate-btn').addEventListener('click', async () => {
            const input = document.getElementById('license-key-input');
            const errorEl = document.getElementById('license-error');
            const key = input.value.trim();

            if (!key) {
                errorEl.textContent = 'Ingresá la clave de licencia';
                errorEl.classList.remove('hidden');
                return;
            }

            try {
                const res = await API.activateLicense(key);
                if (res.success) {
                    const lic = await API.getLicenseStatus();
                    this.showApp(lic);
                    this.bindNav();
                    this.navigateTo('dashboard');
                } else {
                    errorEl.textContent = res.message;
                    errorEl.classList.remove('hidden');
                }
            } catch (err) {
                errorEl.textContent = `Error: ${err.message}`;
                errorEl.classList.remove('hidden');
            }
        });

        // Enter key
        document.getElementById('license-key-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') document.getElementById('license-activate-btn').click();
        });
    },

    showApp(lic) {
        document.getElementById('license-gate').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');

        // Show client name if available
        if (lic && lic.client_name) {
            const badge = document.getElementById('license-badge');
            if (badge) badge.title = `Cliente: ${lic.client_name}`;
        }
    },

    bindNav() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                if (page) this.navigateTo(page);
            });
        });
    },

    async navigateTo(page) {
        this.currentPage = page;

        // Update nav
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        const activeLink = document.querySelector(`[data-page="${page}"]`);
        if (activeLink) activeLink.classList.add('active');

        // Show page
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const pageEl = document.getElementById(`page-${page}`);
        if (pageEl) pageEl.classList.add('active');

        // Re-render Lucide icons for the new page
        if (window.rerenderIcons) window.rerenderIcons();

        // Init page
        switch (page) {
            case 'dashboard':  await DashboardPage.init();  break;
            case 'analytics':  await AnalyticsPage.init();  break;
            case 'settings':   await SettingsPage.init();   break;
            case 'properties': PropertiesPage.init();       break;
            case 'sync':       await SyncPage.init();       break;
        }
    },

    toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const t = document.createElement('div');
        t.className = `toast ${type}`;
        t.textContent = message;
        container.appendChild(t);
        setTimeout(() => t.remove(), 4000);
    }
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
