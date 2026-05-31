# ui/actions/edit_actions.py
from PySide6.QtWidgets import QMessageBox
from ui.dialogs.part_dialog import PartDialog
from ui.dialogs.batch_edit_dialog import BatchEditDialog
from ui.actions.image_actions import ImageActions

class EditActions:
    def __init__(self, main_window):
        self.main = main_window

    def add_part(self):
        dialog = PartDialog(self.main, db=self.main.db, start_depth=self.main.selector_tree_depth)
        if dialog.exec():
            data = dialog.get_data()
            image_files = data.pop('image_files', [])
            part_id = self.main.db.create_part(data)
            if part_id:
                if image_files:
                    img_paths = ImageActions.save_images_for_part(self.main.db, part_id, image_files)
                    update_data = {k: v for k, v in img_paths.items() if v}
                    if update_data:
                        part = self.main.db.get_part(part_id)
                        part.update(update_data)
                        self.main.db.update_part(part_id, part)
                self.main.view_actions.refresh_all()
                QMessageBox.information(self.main, "✅", "Деталь добавлена!")
            else:
                QMessageBox.critical(self.main, "Ошибка", "Не удалось создать деталь.")

    def edit_part(self):
        pid = self.main.parts_table.get_selected_part_id()
        if pid:
            part = self.main.db.get_part(pid)
            if part:
                dialog = PartDialog(self.main, part_data=part, db=self.main.db, start_depth=self.main.selector_tree_depth)
                if dialog.exec():
                    data = dialog.get_data()
                    image_files = data.pop('image_files', [])
                    self.main.db.update_part(pid, data)
                    if image_files:
                        img_paths = ImageActions.save_images_for_part(self.main.db, pid, image_files)
                        update_data = {k: v for k, v in img_paths.items() if v}
                        if update_data:
                            part_updated = self.main.db.get_part(pid)
                            part_updated.update(update_data)
                            self.main.db.update_part(pid, part_updated)
                    self.main.view_actions.refresh_all()
                    QMessageBox.information(self.main, "✅", "Деталь обновлена!")
        else:
            QMessageBox.warning(self.main, "⚠️", "Выберите строку")

    def delete_part(self):
        pid = self.main.parts_table.get_selected_part_id()
        if not pid:
            return
        name = self.main.db.get_part(pid)['name']
        if QMessageBox.question(self.main, "❓", f"Удалить '{name}'?") == QMessageBox.Yes:
            self.main.db.delete_part(pid)
            self.main.view_actions.refresh_all()
            QMessageBox.information(self.main, "✅", "Удалено")

    def batch_edit(self):
        part_ids = self.main.parts_table.get_selected_part_ids()
        if len(part_ids) < 2:
            QMessageBox.warning(self.main, "Предупреждение", "Выберите хотя бы две детали для пакетного редактирования.")
            return
        dialog = BatchEditDialog(self.main, part_ids, self.main.db)
        if dialog.exec():
            self.main.view_actions.refresh_all()
            QMessageBox.information(self.main, "Готово", f"Обновлено {len(part_ids)} деталей.")

    def on_batch_selection_changed(self, count):
        self.main.batch_edit_btn.setEnabled(count >= 2)