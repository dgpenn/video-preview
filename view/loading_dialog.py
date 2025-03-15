from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setLayout(QVBoxLayout())
        self.label = QLabel("Please wait...")
        self.label.setObjectName("LoadingLabel")
        self.layout().addWidget(self.label)
        self.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_text(self, text: str):
        self.label.setText(text)
