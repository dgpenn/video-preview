from view.selection_dialog import SelectionDialog
from model.metadata import Series


class DialogController:
    def __init__(self, dialog: SelectionDialog, data: Series):
        self._populate_dialog(dialog, data)

    def _populate_dialog(self, dialog, data):
        dialog.clear()
        for x in data:
            if x.is_valid():
                dialog.add_item(f"[{x.source}] {x.name} ({x.year})", x)
