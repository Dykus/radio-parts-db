import { fetchJSON, loadCategoriesFromAPI } from './api.js';
import { escapeHtml, getAllDescendantIds } from './utils.js';
import { loadSettings } from './settings.js';

let flatCategories = [];
let currentCategoryIds = [];

export function getCurrentCategoryIds() { return currentCategoryIds; }
export function setCurrentCategoryIds(ids) { currentCategoryIds = ids; }
export function getFlatCategories() { return flatCategories; }

export async function initCategories() {
    flatCategories = await loadCategoriesFromAPI();
    renderCategoryTree();
}

function renderCategoryTree() {
    const container = document.getElementById('categoriesTree');
    if (!flatCategories.length) {
        container.innerHTML = '<div class="p-3">Нет категорий</div>';
        return;
    }
    container.innerHTML = buildTreeHTML(flatCategories);
    attachToggleHandlers(container);
    attachCategoryClickHandlers(container);
}

function buildTreeHTML(cats) {
    const map = Object.fromEntries(cats.map(c => [c.id, { ...c, children: [] }]));
    const roots = [];
    cats.forEach(cat => {
        if (!cat.parent_id || !map[cat.parent_id]) roots.push(map[cat.id]);
        else map[cat.parent_id].children.push(map[cat.id]);
    });
    roots.sort((a,b) => a.name.localeCompare(b.name));
    roots.forEach(node => sortChildren(node));
    function sortChildren(node) {
        node.children.sort((a,b) => a.name.localeCompare(b.name));
        node.children.forEach(sortChildren);
    }
    function render(node, level) {
        const hasKids = node.children.length > 0;
        const icon = hasKids ? '<span class="toggle-icon">▶</span>' : '<span style="width:20px;display:inline-block"></span>';
        const html = `<div class="category-item" data-id="${node.id}" style="margin-left:${level*20}px">${icon} ${escapeHtml(node.name)}</div>`;
        let kidsHtml = '';
        if (hasKids) kidsHtml = `<div class="category-children">${node.children.map(ch => render(ch, level+1)).join('')}</div>`;
        return `<div class="category-node">${html}${kidsHtml}</div>`;
    }
    return roots.map(r => render(r, 0)).join('');
}

function attachToggleHandlers(container) {
    container.querySelectorAll('.toggle-icon').forEach(icon => {
        icon.removeEventListener('click', toggleHandler);
        icon.addEventListener('click', toggleHandler);
    });
    function toggleHandler(e) {
        e.stopPropagation();
        const icon = e.currentTarget;
        const childrenDiv = icon.closest('.category-node')?.querySelector('.category-children');
        if (childrenDiv) {
            if (childrenDiv.style.display === 'none') {
                childrenDiv.style.display = 'block';
                icon.textContent = '▼';
            } else {
                childrenDiv.style.display = 'none';
                icon.textContent = '▶';
            }
        }
    }
}

function attachCategoryClickHandlers(container) {
    container.querySelectorAll('.category-item').forEach(el => {
        el.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-icon')) return;
            const id = parseInt(el.dataset.id);
            currentCategoryIds = getAllDescendantIds(id, flatCategories);
            document.querySelectorAll('#categoriesTree .category-item').forEach(c => c.classList.remove('category-active'));
            el.classList.add('category-active');
            // Сигнал для перезагрузки таблицы (будет вызван из app.js)
            if (window.onCategoryChanged) window.onCategoryChanged();
        });
    });
}

export function expandAllCategories() {
    const container = document.getElementById('categoriesTree');
    container.querySelectorAll('.category-children').forEach(el => el.style.display = 'block');
    container.querySelectorAll('.toggle-icon').forEach(icon => { if (icon.textContent === '▶') icon.textContent = '▼'; });
}

export function collapseAllCategories() {
    const container = document.getElementById('categoriesTree');
    container.querySelectorAll('.category-children').forEach(el => el.style.display = 'none');
    container.querySelectorAll('.toggle-icon').forEach(icon => { if (icon.textContent === '▼') icon.textContent = '▶'; });
}