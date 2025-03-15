#!/usr/bin/env python

import sys
from pathlib import Path
from view.metadata_preview import MetadataPreview
from view.video_preview import VideoPreview
from view.video_tree import VideoTree
from controller.primary import PrimaryController
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import QThread, pyqtSignal


class RenameWorker(QThread):
    rename_finished = pyqtSignal()

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        self.controller.rename_video()
        self.rename_finished.emit()


class Previewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Previewer")
        self.preview = VideoPreview()
        self.video_tree_widget = VideoTree()
        self.metadata_preview = MetadataPreview()
        self.controller = PrimaryController(
            self.video_tree_widget, self.preview, self.metadata_preview, parent=self
        )

        self.rename_button = QPushButton()
        self.rename_button.setMinimumHeight(50)
        self.rename_button.setText("Rename")
        self.rename_button.clicked.connect(self._process_rename)

        self.left_side_layout = QVBoxLayout()
        self.left_side_layout.addWidget(self.preview, 1)
        self.left_side_layout.addWidget(self.video_tree_widget, 1)

        self.right_side_layout = QVBoxLayout()
        self.right_side_layout.addWidget(self.metadata_preview)

        self.panes_layout = QHBoxLayout()
        self.panes_layout.addLayout(self.left_side_layout, 1)
        self.panes_layout.addLayout(self.right_side_layout, 1)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.panes_layout)
        self.main_layout.addWidget(self.rename_button)

        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        self.worker = None

    def showEvent(self, event):
        super().showEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _process_rename(self):
        self.setDisabled(True)
        self.worker = RenameWorker(self.controller)
        self.worker.rename_finished.connect(self.on_rename_finished)
        self.worker.start()

    def on_rename_finished(self):
        self.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Previewer()
    window.show()
    stylesheet = Path("style.qss")
    if stylesheet.is_file():
        app.setStyleSheet(stylesheet.read_text())
    sys.exit(app.exec())
