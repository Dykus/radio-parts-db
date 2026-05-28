const STORAGE_KEYS = {
    CATEGORY_TREE_DEPTH: 'category_tree_depth',
    LOCATION_TREE_DEPTH: 'location_tree_depth',
    SELECTOR_TREE_DEPTH: 'selector_tree_depth'
};

export function loadSettings() {
    return {
        categoryDepth: parseInt(localStorage.getItem(STORAGE_KEYS.CATEGORY_TREE_DEPTH) || '0'),
        locationDepth: parseInt(localStorage.getItem(STORAGE_KEYS.LOCATION_TREE_DEPTH) || '0'),
        selectorDepth: parseInt(localStorage.getItem(STORAGE_KEYS.SELECTOR_TREE_DEPTH) || '0')
    };
}

export function saveCategoryDepth(depth) {
    localStorage.setItem(STORAGE_KEYS.CATEGORY_TREE_DEPTH, depth);
}

export function saveLocationDepth(depth) {
    localStorage.setItem(STORAGE_KEYS.LOCATION_TREE_DEPTH, depth);
}

export function saveSelectorDepth(depth) {
    localStorage.setItem(STORAGE_KEYS.SELECTOR_TREE_DEPTH, depth);
}