# ui/handlers/selection_handler.py
from PySide6.QtWidgets import QMessageBox
from ui.dialogs.part_viewer import PartViewer

class SelectionHandler:
    def __init__(self, main_window):
        self.main = main_window

    def on_selection_changed(self, part_id):
        if not part_id:
            self.main.right_panel.update_content(None)
            return
        part = self.main.db.get_part(part_id)
        if part:
            self.main.right_panel.update_content(part)

    def view_part(self, part_id):
        part = self.main.db.get_part(part_id)
        if part:
            viewer = PartViewer(part, self.main.db, self.main)
            viewer.show()