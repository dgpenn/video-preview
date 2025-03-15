#!/usr/bin/env python

from pathlib import Path
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import (
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class VideoTree(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.local_root = Path("")
        self.model = QFileSystemModel()
        self.tree = QTreeView()

        self.model.setRootPath("")
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(""))

        header = self.tree.header()
        for section in range(1, header.count()):
            header.hideSection(section)
        header.hide()

        self.set_root_button = QPushButton(
            f"Select Video Folder {self.local_root.name}"
        )
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.set_root_button)
        self.main_layout.addWidget(self.tree)
        self.setLayout(self.main_layout)

    def _set_root_path(self, root_path: Path):
        """Set the root path to search for videos"""
        if root_path.is_dir():
            self.local_root = root_path
            self.set_root_button.setText(f"Folder: {self.local_root.name}")
            index = self.model.index(root_path.as_posix())
            self.tree.setRootIndex(index)

    def refresh(self):
        """Refresh the Video Tree View"""
        self.model.setRootPath(self.local_root.as_posix())
        self.tree.setRootIndex(self.model.index(self.local_root.as_posix()))
