import { loadCategories, setOnCategorySelect, getCurrentCategoryIds, getFlatCategories } from './categories.js';
import { loadParts, setCurrentFilter, setCurrentSearchText, setCurrentCategoryIds } from './parts.js';
import { initModals } from './modals.js';
import { loadSettings } from './settings.js';

async function init() {
    const settings = loadSettings();
    
    // Инициализация модальных окон
    initModals();
    
    // Устанавливаем обработчик изменения категории
    setOnCategorySelect((ids) => {
        setCurrentCategoryIds(ids);
    });
    
    // Загружаем категории и детали
    await loadCategories();
    await loadParts();
    
    // Применяем сохранённые настройки фильтра и поиска
    if (settings.filter) {
        const filterBtn = document.querySelector(`.filter-btn[data-filter="${settings.filter}"]`);
        if (filterBtn) filterBtn.click();
        else setCurrentFilter(settings.filter);
    }
    if (settings.searchText) {
        document.getElementById('searchInput').value = settings.searchText;
        setCurrentSearchText(settings.searchText);
    }
    
    // Кнопка обновления
    document.getElementById('refreshBtn').addEventListener('click', async () => {
        await loadCategories();
        await loadParts();
    });
    
    // Фильтры
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setCurrentFilter(btn.dataset.filter);
        });
    });
    
    // Поиск
    document.getElementById('searchInput').addEventListener('input', (e) => {
        setCurrentSearchText(e.target.value);
    });
}

init();