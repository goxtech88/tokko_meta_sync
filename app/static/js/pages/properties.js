/**
 * pages/properties.js – Properties catalog page controller.
 */
const PropertiesPage = {
    init() {
        document.getElementById('refresh-props-btn').addEventListener('click', () => this.load());
    },

    async load() {
        const grid = document.getElementById('properties-grid');
        grid.innerHTML = '<p class="muted">Cargando propiedades…</p>';

        try {
            const data = await API.getProperties(100);
            if (data.error) {
                grid.innerHTML = `<p class="error-text">⚠️ ${data.error}</p>`;
                return;
            }

            const props = data.properties || [];
            if (!props.length) {
                grid.innerHTML = '<p class="muted">No se encontraron propiedades</p>';
                return;
            }

            grid.innerHTML = props.map(p => this._card(p)).join('');
            App.toast(`${props.length} propiedades cargadas`, 'success');
        } catch (err) {
            grid.innerHTML = `<p class="error-text">Error: ${err.message}</p>`;
        }
    },

    _card(p) {
        const price = p.price
            ? `${p.currency || 'USD'} ${Number(p.price).toLocaleString('es-AR')}`
            : 'Consultar';

        const details = [];
        if (p.bedrooms) details.push(`🛏 ${p.bedrooms}`);
        if (p.bathrooms) details.push(`🚿 ${p.bathrooms}`);
        if (p.surface) details.push(`📐 ${p.surface} m²`);

        const thumb = p.thumbnail || '';
        const imgTag = thumb
            ? `<img class="property-thumb" src="${thumb}" alt="${p.title}" loading="lazy" onerror="this.style.display='none'">`
            : `<div class="property-thumb" style="display:flex;align-items:center;justify-content:center;font-size:2rem;color:var(--text-3)">🏠</div>`;

        return `
            <div class="property-card glass">
                ${imgTag}
                <div class="property-body">
                    <div class="property-title" title="${p.title || ''}">${p.title || '—'}</div>
                    <div class="property-address" title="${p.address || ''}">${p.address || ''}</div>
                    <div class="property-meta">${details.join(' &nbsp;·&nbsp; ')}</div>
                    <div class="property-price">${price}</div>
                </div>
            </div>
        `;
    }
};
