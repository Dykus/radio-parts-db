# ui/actions/view_actions.py
from PySide6.QtWidgets import QMessageBox
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.help_dialog import HelpDialog

class ViewActions:
    def __init__(self, main_window):
        self.main = main_window
        self.current_filter = "all"
        self.selected_location_path = None
        self.selected_category_id = None

    def apply_filter(self, filter_type):
        self.current_filter = filter_type
        for btn in [self.main.filter_all_btn, self.main.filter_stock_btn,
                    self.main.filter_low_btn, self.main.filter_out_btn]:
            btn.setChecked(False)
        if filter_type == "all":
            self.main.filter_all_btn.setChecked(True)
        elif filter_type == "in_stock":
            self.main.filter_stock_btn.setChecked(True)
        elif filter_type == "low_stock":
            self.main.filter_low_btn.setChecked(True)
        elif filter_type == "out_of_stock":
            self.main.filter_out_btn.setChecked(True)
        self.refresh_table()
        self.update_status()

    def on_all_filter(self):
        self.selected_category_id = None
        self.main.category_tree._on_show_all_clicked()
        self.apply_filter("all")

    def on_category_selected(self, cat_id):
        self.selected_category_id = cat_id
        self.refresh_table()
        self.update_status()

    def filter_by_location(self, location_path):
        self.selected_location_path = location_path
        self.refresh_table()
        self.update_status()

    def refresh_all(self):
        self.main.category_tree.load_categories()
        self.main.right_panel.load_tree()
        self.refresh_table()
        self.update_status()

    def refresh_table(self):
        self.main.parts_table.load_data(self.selected_category_id, self.current_filter, self.selected_location_path)

    def filter_table(self, text):
        self.main.parts_table.proxy_model.set_search_text(text)

    def focus_search(self):
        self.main.search_edit.setFocus()
        self.main.search_edit.selectAll()

    def update_status(self):
        s = self.main.db.get_stats()
        loc = self.selected_location_path or "Везде"
        cat_text = "Все" if self.selected_category_id is None else "Категория"
        self.main.status.showMessage(f"📦 {s['total_parts']} | 💰 {s['total_value']:.0f}₽ | 📍 {loc} | 🏷 {cat_text}")

    def on_category_depth_changed(self, index):
        depth = self.main.category_depth_inline.currentData()
        self.main.category_tree_depth = depth
        self.main.category_tree.start_depth = depth
        self.main.category_tree.load_categories()
        self.main.saved_settings['category_tree_depth'] = depth
        self.main.settings_handler.save_settings()

    def on_location_depth_changed(self, index):
        depth = self.main.location_depth_inline.currentData()
        self.main.location_tree_depth = depth
        self.main.right_panel.start_depth = depth
        self.main.right_panel.load_tree()
        self.main.saved_settings['location_tree_depth'] = depth
        self.main.settings_handler.save_settings()

    def on_location_depth_from_widget(self, depth):
        self.main.location_tree_depth = depth
        self.main.saved_settings['location_tree_depth'] = depth
        idx = self.main.location_depth_inline.findData(depth)
        if idx >= 0:
            self.main.location_depth_inline.setCurrentIndex(idx)
        self.main.settings_handler.save_settings()

    def open_settings(self):
        dialog = SettingsDialog(self.main, settings=self.main.saved_settings)
        dialog.category_depth_changed.connect(self._on_category_depth_from_settings)
        dialog.location_depth_changed.connect(self._on_location_depth_from_settings)
        dialog.selector_depth_changed.connect(self._on_selector_depth_from_settings)
        if dialog.exec():
            new_settings = dialog.get_settings()
            self.main.saved_settings.update(new_settings)
            self.main.category_tree_depth = new_settings.get('category_tree_depth', 0)
            self.main.location_tree_depth = new_settings.get('location_tree_depth', 0)
            self.main.selector_tree_depth = new_settings.get('selector_tree_depth', 0)
            self.main.settings_handler.save_settings()
            self.main.category_depth_inline.setCurrentIndex(self.main.category_depth_inline.findData(self.main.category_tree_depth))
            self.main.location_depth_inline.setCurrentIndex(self.main.location_depth_inline.findData(self.main.location_tree_depth))
            QMessageBox.information(self.main, "✅", "Настройки сохранены!")

    def _on_category_depth_from_settings(self, depth):
        self.main.category_tree_depth = depth
        self.main.category_tree.start_depth = depth
        self.main.category_tree.load_categories()

    def _on_location_depth_from_settings(self, depth):
        self.main.location_tree_depth = depth
        self.main.right_panel.start_depth = depth
        self.main.right_panel.load_tree()

    def _on_selector_depth_from_settings(self, depth):
        self.main.selector_tree_depth = depth

    def open_help(self):
        dialog = HelpDialog(self.main)
        dialog.exec()

    def show_about(self):
        dialog = AboutDialog(self.main)
        dialog.exec()