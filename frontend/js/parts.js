import { loadPartsFromAPI } from './api.js';
import { escapeHtml, formatPackageWithDimensions } from './utils.js';
import { getCurrentCategoryIds } from './categories.js';

let allParts = [];
let currentFilter = 'all';
let currentSearchText = '';

export function getCurrentFilter() { return currentFilter; }
export function setCurrentFilter(filter) { currentFilter = filter; }
export function getCurrentSearchText() { return currentSearchText; }
export function setCurrentSearchText(text) { currentSearchText = text; }

export async function loadParts() {
    const parts = await loadPartsFromAPI();
    let filtered = parts;
    const catIds = getCurrentCategoryIds();
    if (catIds.length) filtered = filtered.filter(p => catIds.includes(Number(p.category_id)));
    if (currentFilter === 'in_stock') filtered = filtered.filter(p => p.quantity > 0);
    else if (currentFilter === 'low_stock') filtered = filtered.filter(p => p.quantity > 0 && p.quantity < 10);
    else if (currentFilter === 'out_of_stock') filtered = filtered.filter(p => p.quantity === 0);
    if (currentSearchText) {
        const search = currentSearchText.toLowerCase();
        filtered = filtered.filter(p =>
            (p.name && p.name.toLowerCase().includes(search)) ||
            (p.part_type && p.part_type.toLowerCase().includes(search)) ||
            (p.package && p.package.toLowerCase().includes(search)) ||
            (p.location && p.location.toLowerCase().includes(search)) ||
            (p.status && p.status.toLowerCase().includes(search))
        );
    }
    allParts = filtered;
    renderTable(allParts);
}

function renderTable(parts) {
    const tbody = document.getElementById('table-body');
    if (!parts.length) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center">Нет деталей</td></tr>';
        return;
    }
    let html = '';
    for (const p of parts) {
        const qty = Number(p.quantity);
        let rowBgColor = '', rowTextColor = '';
        if (qty > 10) { rowBgColor = '#c8e6c9'; rowTextColor = '#000000'; }
        else if (qty > 0) { rowBgColor = '#fff9c4'; rowTextColor = '#000000'; }
        else { rowBgColor = '#ffcdd2'; rowTextColor = '#000000'; }

        let statusBgColor = '', statusTextColor = '';
        const statusText = (p.status || '').toLowerCase();
        if (statusText === 'новое' || statusText === 'отличное') { statusBgColor = '#a5d6a7'; statusTextColor = '#1b5e20'; }
        else if (statusText === 'б/у проверено') { statusBgColor = '#90caf9'; statusTextColor = '#0d3c5e'; }
        else if (statusText === 'б/у не проверено') { statusBgColor = '#fff59d'; statusTextColor = '#5d4b0a'; }
        else if (statusText === 'плохое') { statusBgColor = '#ffcc80'; statusTextColor = '#5d2e0a'; }
        else if (statusText === 'неисправно') { statusBgColor = '#ef9a9a'; statusTextColor = '#8b0000'; }
        else { statusBgColor = '#e0e0e0'; statusTextColor = '#000000'; }

        const nominal = (p.value_numeric !== null && p.value_numeric !== undefined && p.value_unit)
            ? `${p.value_numeric}${p.value_unit}`
            : (p.value_numeric !== null ? p.value_numeric : '-');
        const dims = {
            diameter_mm: p.diameter_mm,
            height_mm: p.height_mm,
            lead_pitch_mm: p.lead_pitch_mm,
            lead_diameter_mm: p.lead_diameter_mm
        };
        const hasPhoto = !!(p.image_path && p.image_path.trim());
        const packageDisplay = formatPackageWithDimensions(p.package, dims, hasPhoto);

        html += `<tr style="background-color: ${rowBgColor}; color: ${rowTextColor};">
            <td style="background-color: inherit; color: inherit;">${p.id}</td>
            <td style="background-color: inherit; color: inherit;"><strong>${escapeHtml(p.name)}</strong></td>
            <td style="background-color: inherit; color: inherit;">${escapeHtml(p.part_type) || '-'}</td>
            <td style="background-color: inherit; color: inherit;">${escapeHtml(nominal)}</td>
            <td style="background-color: inherit; color: inherit;">${escapeHtml(packageDisplay)}</td>
            <td class="text-center" style="background-color: inherit; color: inherit;">${qty}</td>
            <td class="text-end" style="background-color: inherit; color: inherit;">${p.price.toFixed(2)} ₽</td>
            <td style="background-color: inherit; color: inherit;">${escapeHtml(p.location) || '-'}</td>
            <td class="status-cell" style="background-color: ${statusBgColor}; color: ${statusTextColor};">${escapeHtml(p.status) || 'Новое'}</td>
            <td style="background-color: inherit; color: inherit;"><button class="btn btn-sm btn-outline-secondary edit-btn" data-id="${p.id}">✏️</button></td>
        </tr>`;
    }
    tbody.innerHTML = html;
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (window.openEditModal) window.openEditModal(parseInt(btn.dataset.id));
        });
    });
}