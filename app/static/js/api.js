/**
 * api.js – Thin wrapper around fetch() for the backend API.
 */
const API = {
    async _req(method, path, body) {
        const opts = { method, headers: { 'Content-Type': 'application/json' } };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(path, opts);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },

    // Settings
    getSettings()          { return this._req('GET', '/api/settings'); },
    saveSettings(data)     { return this._req('PUT', '/api/settings', data); },
    testTokko()            { return this._req('POST', '/api/settings/test-tokko'); },
    testMeta()             { return this._req('POST', '/api/settings/test-meta'); },
    testGA4()              { return this._req('POST', '/api/settings/test-ga4'); },

    // Properties
    getProperties(limit=50){ return this._req('GET', `/api/properties?limit=${limit}`); },

    // Sync
    runSync()              { return this._req('POST', '/api/sync/run'); },
    getSyncHistory()       { return this._req('GET', '/api/sync/history'); },
    getSyncStatus()        { return this._req('GET', '/api/sync/status'); },

    // License
    getLicenseStatus()     { return this._req('GET', '/api/license/status'); },
    activateLicense(key)   { return this._req('POST', '/api/license/activate', { key }); },

    // Analytics
    getAnalytics(days=30)  { return this._req('GET', `/api/analytics?days=${days}`); },
};
