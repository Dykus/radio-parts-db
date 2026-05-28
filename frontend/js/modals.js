import { savePartToAPI, getPart, loadCategoriesFromAPI } from './api.js';
import { escapeHtml, buildCategoryPath, getAllDescendantIds } from './utils.js';
import { getFlatCategories, setCurrentCategoryIds, initCategories } from './categories.js';
import { loadParts, setCurrentCategoryIds as setPartsCategoryIds } from './parts.js';
import { updateStats } from './stats.js';

let partModal = null;
let categoryModal = null;
let flatCategories = [];

/**
 * Инициализация модальных окон и обработчиков
 */
export async function initModals() {
    // Получаем плоский список категорий (может быть ещё не загружен)
    flatCategories = getFlatCategories();
    if (!flatCategories.length) {
        flatCategories = await loadCategoriesFromAPI();
    }

    partModal = new bootstrap.Modal(document.getElementById('partModal'));
    categoryModal = new bootstrap.Modal(document.getElementById('categoryModal'));

    document.getElementById('addPartBtn').addEventListener('click', () => openEditModal(null));
    document.getElementById('selectCategoryBtn').addEventListener('click', openCategoryModal);
    document.getElementById('assembleNameBtn').addEventListener('click', assembleName);
    document.getElementById('savePartBtn').addEventListener('click', savePart);
}

/**
 * Открыть модалку редактирования/добавления
 * @param {number|null} id - id детали или null для новой
 */
export async function openEditModal(id = null) {
    // Сброс формы
    document.getElementById('partForm').reset();
    document.getElementById('partId').value = '';
    document.getElementById('name').value = '';
    document.getElementById('categoryPath').value = '';
    document.getElementById('partType').value = '';
    document.getElementById('valueNumeric').value = '';
    document.getElementById('valueUnit').innerHTML = '<option value="">-- единица --</option>';
    document.getElementById('package').value = '';
    document.getElementById('diameter_mm').value = '';
    document.getElementById('height_mm').value = '';
    document.getElementById('lead_pitch_mm').value = '';
    document.getElementById('lead_diameter_mm').value = '';
    document.getElementById('status').value = 'Новое';
    document.getElementById('manufacturer').value = '';
    document.getElementById('mpn').value = '';
    document.getElementById('quantity').value = 0;
    document.getElementById('price').value = 0;
    document.getElementById('locPlace').value = '';
    document.getElementById('locContainer').value = '';
    document.getElementById('locShelf').value = '';
    document.getElementById('locSection').value = '';
    document.getElementById('imagePath').value = '';
    document.getElementById('datasheetPath').value = '';
    document.getElementById('revisionDate').value = '';
    document.getElementById('notes').value = '';
    document.getElementById('capacitorDims').style.display = 'none';

    if (id) {
        try {
            const part = await getPart(id);
            document.getElementById('partId').value = part.id;
            document.getElementById('name').value = part.name || '';
            if (part.category_id && flatCategories.length) {
                const path = buildCategoryPath(part.category_id, flatCategories);
                document.getElementById('categoryPath').value = path;
                updateUnitsByCategory(path);
            }
            document.getElementById('partType').value = part.part_type || '';
            if (part.value_numeric !== null && part.value_numeric !== undefined) {
                document.getElementById('valueNumeric').value = part.value_numeric;
            }
            if (part.value_unit) {
                const sel = document.getElementById('valueUnit');
                let exists = false;
                for (let i = 0; i < sel.options.length; i++) {
                    if (sel.options[i].value === part.value_unit) exists = true;
                }
                if (!exists) {
                    const opt = document.createElement('option');
                    opt.value = part.value_unit;
                    opt.text = part.value_unit;
                    sel.appendChild(opt);
                }
                sel.value = part.value_unit;
            }
            document.getElementById('package').value = part.package || '';
            if (part.diameter_mm) document.getElementById('diameter_mm').value = part.diameter_mm;
            if (part.height_mm) document.getElementById('height_mm').value = part.height_mm;
            if (part.lead_pitch_mm) document.getElementById('lead_pitch_mm').value = part.lead_pitch_mm;
            if (part.lead_diameter_mm) document.getElementById('lead_diameter_mm').value = part.lead_diameter_mm;
            document.getElementById('status').value = part.status || 'Новое';
            document.getElementById('manufacturer').value = part.manufacturer || '';
            document.getElementById('mpn').value = part.mpn || '';
            document.getElementById('quantity').value = part.quantity || 0;
            document.getElementById('price').value = part.price || 0;
            if (part.location) {
                const loc = part.location.split('/');
                if (loc[0]) document.getElementById('locPlace').value = loc[0].trim();
                if (loc[1]) document.getElementById('locContainer').value = loc[1].trim();
                if (loc[2]) document.getElementById('locShelf').value = loc[2].trim();
                if (loc[3]) document.getElementById('locSection').value = loc[3].trim();
            }
            document.getElementById('imagePath').value = part.image_path || '';
            document.getElementById('datasheetPath').value = part.datasheet_path || '';
            if (part.revision_date) document.getElementById('revisionDate').value = part.revision_date;
            document.getElementById('notes').value = part.notes || '';
        } catch (e) {
            alert('Ошибка загрузки детали: ' + e.message);
            return;
        }
    }
    partModal.show();
}

/**
 * Сохранить деталь (новая или обновление)
 */
async function savePart() {
    const id = document.getElementById('partId').value;
    let catId = null;
    const catPath = document.getElementById('categoryPath').value;
    if (catPath && flatCategories.length) {
        const target = catPath.split('/').pop().trim();
        const possible = flatCategories.filter(c => c.name === target);
        for (let c of possible) {
            if (buildCategoryPath(c.id, flatCategories) === catPath) {
                catId = c.id;
                break;
            }
        }
    }
    const location = [
        document.getElementById('locPlace').value,
        document.getElementById('locContainer').value,
        document.getElementById('locShelf').value,
        document.getElementById('locSection').value
    ].filter(v => v.trim()).join(' / ');

    const numeric = parseFloat(document.getElementById('valueNumeric').value);
    const unit = document.getElementById('valueUnit').value;
    const data = {
        name: document.getElementById('name').value.trim(),
        category_id: catId,
        part_type: document.getElementById('partType').value.trim(),
        package: document.getElementById('package').value.trim(),
        manufacturer: document.getElementById('manufacturer').value.trim(),
        mpn: document.getElementById('mpn').value.trim(),
        quantity: parseInt(document.getElementById('quantity').value) || 0,
        price: parseFloat(document.getElementById('price').value) || 0,
        location: location,
        status: document.getElementById('status').value,
        image_path: document.getElementById('imagePath').value.trim(),
        datasheet_path: document.getElementById('datasheetPath').value.trim(),
        revision_date: document.getElementById('revisionDate').value || null,
        notes: document.getElementById('notes').value.trim(),
        value_numeric: isNaN(numeric) ? null : numeric,
        value_unit: unit || null,
        value_raw: document.getElementById('valueNumeric').value.trim() + (unit ? ' ' + unit : ''),
        diameter_mm: parseFloat(document.getElementById('diameter_mm').value) || null,
        height_mm: parseFloat(document.getElementById('height_mm').value) || null,
        lead_pitch_mm: parseFloat(document.getElementById('lead_pitch_mm').value) || null,
        lead_diameter_mm: parseFloat(document.getElementById('lead_diameter_mm').value) || null
    };
    if (!data.name) {
        alert('Наименование обязательно');
        return;
    }
    try {
        await savePartToAPI(data, id || null);
        partModal.hide();
        // Обновляем таблицу и статистику
        await loadParts();
        await updateStats();
        // Если в детали изменилась категория, может понадобиться обновить категории в дереве?
        // Пока просто перезагрузим дерево категорий (чтобы обновить счетчики)
        await initCategories();
    } catch (e) {
        alert('Ошибка сохранения: ' + e.message);
    }
}

/**
 * Собрать название из номинала, единицы, напряжения и корпуса
 */
function assembleName() {
    const num = document.getElementById('valueNumeric').value.trim();
    const unit = document.getElementById('valueUnit').value;
    const catPath = document.getElementById('categoryPath').value;
    const pkg = document.getElementById('package').value.trim();
    let voltage = '';
    if (catPath) {
        const last = catPath.split('/').pop().trim();
        if (/\d+V/i.test(last)) {
            voltage = last.replace('V', 'В').replace('v', 'В');
        }
    }
    const val = num && unit ? num + unit : (num || unit);
    const name = [val, voltage, pkg].filter(v => v).join(' ');
    if (name) {
        document.getElementById('name').value = name;
    } else {
        alert('Заполните номинал или выберите категорию с напряжением');
    }
}

/**
 * Обновить список единиц измерения и показать/скрыть размеры конденсатора
 * @param {string} categoryPath - путь категории (через /)
 */
function updateUnitsByCategory(categoryPath) {
    const low = categoryPath.toLowerCase();
    let units = [];
    if (low.includes('конденсатор')) {
        units = ['пФ', 'нФ', 'мкФ', 'Ф'];
    } else if (low.includes('резистор')) {
        units = ['Ом', 'кОм', 'МОм'];
    } else if (low.includes('катушк') || low.includes('индуктивност')) {
        units = ['мкГн', 'мГн', 'Гн'];
    } else {
        units = ['Ом', 'кОм', 'МОм', 'пФ', 'нФ', 'мкФ', 'Ф', 'Гн', 'мГн', 'мкГн', 'В', 'А', 'мА'];
    }
    const sel = document.getElementById('valueUnit');
    const old = sel.value;
    sel.innerHTML = '<option value="">-- выберите --</option>';
    units.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u;
        opt.text = u;
        sel.appendChild(opt);
    });
    if (units.includes(old)) sel.value = old;

    const dimsBlock = document.getElementById('capacitorDims');
    if (low.includes('конденсатор')) {
        dimsBlock.style.display = 'block';
    } else {
        dimsBlock.style.display = 'none';
    }
}

/**
 * Открыть модалку выбора категории
 */
function openCategoryModal() {
    const modalBody = document.getElementById('categoryTreeModal');
    if (flatCategories.length) {
        modalBody.innerHTML = buildCategoryTreeHTML(flatCategories);
        attachToggleHandlers(modalBody);
        modalBody.querySelectorAll('.category-item').forEach(el => {
            el.addEventListener('click', (e) => {
                if (e.target.classList.contains('toggle-icon')) return;
                const id = parseInt(el.dataset.id);
                const path = buildCategoryPath(id, flatCategories);
                document.getElementById('categoryPath').value = path;
                updateUnitsByCategory(path);
                categoryModal.hide();
            });
        });
    } else {
        modalBody.innerHTML = '<div class="p-3">Загрузка...</div>';
    }
    categoryModal.show();
}

/**
 * Построить HTML дерева категорий (копия из categories.js, но можно переиспользовать)
 */
function buildCategoryTreeHTML(cats) {
    const map = Object.fromEntries(cats.map(c => [c.id, { ...c, children: [] }]));
    const roots = [];
    cats.forEach(cat => {
        if (!cat.parent_id || !map[cat.parent_id]) roots.push(map[cat.id]);
        else map[cat.parent_id].children.push(map[cat.id]);
    });
    roots.sort((a, b) => a.name.localeCompare(b.name));
    roots.forEach(node => sortChildren(node));
    function sortChildren(node) {
        node.children.sort((a, b) => a.name.localeCompare(b.name));
        node.children.forEach(sortChildren);
    }
    function render(node, level) {
        const hasKids = node.children.length > 0;
        const icon = hasKids ? '<span class="toggle-icon">▶</span>' : '<span style="width:20px;display:inline-block"></span>';
        const html = `<div class="category-item" data-id="${node.id}" style="margin-left:${level * 20}px">${icon} ${escapeHtml(node.name)}</div>`;
        let kidsHtml = '';
        if (hasKids) {
            kidsHtml = `<div class="category-children">${node.children.map(ch => render(ch, level + 1)).join('')}</div>`;
        }
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