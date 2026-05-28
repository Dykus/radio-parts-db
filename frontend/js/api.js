// API-вызовы к бэкенду
const API_BASE = 'http://localhost:8000';

/**
 * Универсальная функция для fetch с обработкой ошибок
 * @param {string} url - относительный URL (начинается с /)
 * @param {object} options - опции fetch (method, headers, body)
 * @returns {Promise<any>} - распарсенный JSON ответ
 */
export async function fetchJSON(url, options = {}) {
    const res = await fetch(API_BASE + url, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return res.json();
}

/**
 * Загрузить список деталей (все, без фильтров на сервере – фильтрация на клиенте)
 * @returns {Promise<Array>}
 */
export async function loadPartsFromAPI() {
    return fetchJSON('/api/parts?limit=2000');
}

/**
 * Загрузить список всех категорий
 * @returns {Promise<Array>}
 */
export async function loadCategoriesFromAPI() {
    return fetchJSON('/api/categories');
}

/**
 * Загрузить статистику (общее количество, стоимость, число мест)
 * @returns {Promise<Object>}
 */
export async function loadStatsFromAPI() {
    return fetchJSON('/api/stats');
}

/**
 * Получить одну деталь по ID
 * @param {number} id
 * @returns {Promise<Object>}
 */
export async function getPart(id) {
    return fetchJSON(`/api/parts/${id}`);
}

/**
 * Сохранить деталь (создать или обновить)
 * @param {object} part - данные детали
 * @param {number|null} id - если указан, то PUT, иначе POST
 * @returns {Promise<Object>}
 */
export async function savePartToAPI(part, id = null) {
    const url = id ? `/api/parts/${id}` : '/api/parts';
    const method = id ? 'PUT' : 'POST';
    return fetchJSON(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(part)
    });
}