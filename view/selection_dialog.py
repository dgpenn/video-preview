#!/usr/bin/env python

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QListWidget,
    QListWidgetItem,
)


class SelectionDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Selection Dialog")
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.list_widget)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

        self._adjust_dialog_width()

    def add_item(self, text: str, data: object) -> None:
        """Add an item to the list widget."""
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, data)
        self.list_widget.addItem(item)
        if not self.list_widget.selectedItems():
            self.list_widget.setCurrentRow(0)

    def get_selected_data(self):
        """Get the data of the selected item."""
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.ItemDataRole.UserRole)
        return None

    def get_item_index_data(self, index: int = 0):
        """Get the data of the item at the specified index."""
        if index < self.list_widget.count():
            item = self.list_widget.item(index)
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def clear(self):
        """Clear the list widget."""
        self.list_widget.clear()

    def _adjust_dialog_width(self):
        """Adjust the dialog width to be wide enough to display items."""
        max_width = 0
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            item_width = (
                self.list_widget.fontMetrics().boundingRect(item.text()).width()
            )
            if item_width > max_width:
                max_width = item_width

        padding = 100
        self.setMinimumWidth(max_width + padding)

    def showEvent(self, event):
        self._adjust_dialog_width()
        super().showEvent(event)
