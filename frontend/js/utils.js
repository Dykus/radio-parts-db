export function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/[&<>]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;'})[m]);
}

export function buildCategoryPath(catId, cats) {
    const map = Object.fromEntries(cats.map(c => [c.id, c]));
    const path = [];
    let cur = map[catId];
    while (cur) {
        path.unshift(cur.name);
        cur = map[cur.parent_id];
    }
    return path.join(' / ');
}

export function getAllDescendantIds(catId, cats) {
    let ids = [catId];
    cats.filter(c => c.parent_id === catId).forEach(child => {
        ids.push(...getAllDescendantIds(child.id, cats));
    });
    return ids;
}

export function formatPackageWithDimensions(pkg, dims, hasPhoto) {
    let parts = [];
    if (pkg) parts.push(pkg);
    if (dims.diameter_mm && dims.height_mm) parts.push(`⌀${dims.diameter_mm}×${dims.height_mm}мм`);
    else if (dims.diameter_mm) parts.push(`⌀${dims.diameter_mm}мм`);
    else if (dims.height_mm) parts.push(`высота ${dims.height_mm}мм`);
    if (dims.lead_pitch_mm) parts.push(`шаг ${dims.lead_pitch_mm}мм`);
    if (dims.lead_diameter_mm) parts.push(`вывод ${dims.lead_diameter_mm}мм`);
    let result = parts.join(' / ') || (pkg || '');
    if (hasPhoto) result = '📷 ' + result;
    return result;
}