import { loadStatsFromAPI } from './api.js';

export async function updateStats() {
    try {
        const stats = await loadStatsFromAPI();
        document.getElementById('stats-area').innerHTML = `
            <div class="col-md-4"><div class="card bg-success text-white"><div class="card-body"><h5>📦 Всего</h5><h2>${stats.total_parts}</h2></div></div></div>
            <div class="col-md-4"><div class="card bg-info text-white"><div class="card-body"><h5>💰 Стоимость</h5><h2>${stats.total_value.toLocaleString()} ₽</h2></div></div></div>
            <div class="col-md-4"><div class="card bg-warning text-white"><div class="card-body"><h5>📍 Мест</h5><h2>${stats.unique_locations || 0}</h2></div></div></div>
        `;
    } catch(e) { console.error(e); }
}