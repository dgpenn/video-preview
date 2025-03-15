#!/usr/bin/env python

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QSizePolicy,
    QSpacerItem,
    QComboBox,
    QWidget,
    QLineEdit,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QTextEdit,
    QHBoxLayout,
    QListWidget,
)


class MetadataPreview(QWidget):
    """A widget to display series metadata."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Query")
        self.search_field.setToolTip("Series Query")
        self.search_field.setObjectName("SearchField")

        self.search_button = QPushButton()
        self.search_button.setText("Search")

        self.series_name_box = QLineEdit()
        self.series_name_box.setPlaceholderText("Series Name")
        self.series_name_box.setToolTip("Series Name")

        self.series_name_box_label = QLabel("Name ")
        self.series_name_box_label.setObjectName("MetadataLabel")

        self.year_box = QLineEdit()
        self.year_box.setPlaceholderText("Series Air Year")
        self.year_box.setToolTip("Series Air Year")

        self.year_box_label = QLabel("Year ")
        self.year_box_label.setObjectName("MetadataLabel")

        self.episode_title_box = QLineEdit()
        self.episode_title_box.setPlaceholderText("Episode Title")
        self.episode_title_box.setToolTip("Episode Title")

        self.episode_title_box_label = QLabel("Title ")
        self.episode_title_box_label.setObjectName("MetadataLabel")

        self.episode_description_box = QTextEdit()
        self.episode_description_box.setPlaceholderText("Episode Description")
        self.episode_description_box.setToolTip("Episode Description")

        self.season_number_box = QLineEdit()
        self.season_number_box.setPlaceholderText("#")
        self.season_number_box.setToolTip("Season Number")

        self.meta_season_label = QLabel("Season ")
        self.meta_season_label.setObjectName("MetadataLabel")
        self.meta_season_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.meta_season_label.setMinimumWidth(
            self.meta_season_label.sizeHint().width()
        )

        self.episode_number_box = QLineEdit()
        self.episode_number_box.setPlaceholderText("#")
        self.episode_number_box.setToolTip("Episode Number")

        self.meta_episode_label = QLabel("Episode ")
        self.meta_episode_label.setObjectName("MetadataLabel")
        self.meta_episode_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.meta_episode_label.setMinimumWidth(
            self.meta_episode_label.sizeHint().width()
        )

        self.episode_range_box = QLineEdit()
        self.episode_range_box.setPlaceholderText("#")
        self.episode_range_box.setToolTip("Optional Episode Number for Range")

        self.meta_episode_range_label = QLabel("-")
        self.meta_episode_range_label.setObjectName("MetadataLabel")
        self.meta_episode_range_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.meta_episode_range_label.setMinimumWidth(
            self.meta_episode_range_label.sizeHint().width()
        )

        self.part_number_box = QLineEdit()
        self.part_number_box.setPlaceholderText("#")
        self.part_number_box.setToolTip("Part Number (Optional)")

        self.part_number_box_label = QLabel("Part ")
        self.part_number_box_label.setObjectName("MetadataLabel")
        self.part_number_box_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.part_number_box_label.setMinimumWidth(
            self.part_number_box_label.sizeHint().width()
        )

        self.search_bar_layout = QHBoxLayout()
        self.search_bar_layout.addWidget(self.search_field, 2)
        self.search_bar_layout.addWidget(self.search_button, 1)

        self.name_layout = QHBoxLayout()
        self.name_layout.addWidget(self.series_name_box_label, 0)
        self.name_layout.addWidget(self.series_name_box, 3)
        self.name_layout.addWidget(self.year_box_label, 0)
        self.name_layout.addWidget(self.year_box, 1)

        self.title_layout = QHBoxLayout()
        self.title_layout.addWidget(self.episode_title_box_label, 0)
        self.title_layout.addWidget(self.episode_title_box, 1)

        self.meta_numbers_layout = QHBoxLayout()
        self.meta_numbers_layout.addWidget(self.meta_season_label, 0)
        self.meta_numbers_layout.addWidget(self.season_number_box, 1)
        self.meta_numbers_layout.addWidget(self.meta_episode_label, 0)
        self.meta_numbers_layout.addWidget(self.episode_number_box, 1)
        self.meta_numbers_layout.addWidget(self.meta_episode_range_label, 0)
        self.meta_numbers_layout.addWidget(self.episode_range_box, 1)
        self.meta_numbers_layout.addWidget(self.part_number_box_label, 0)
        self.meta_numbers_layout.addWidget(self.part_number_box, 1)

        self.meta_layout = QVBoxLayout()
        self.meta_layout.addLayout(self.name_layout)
        self.meta_layout.addLayout(self.title_layout)
        self.meta_layout.addLayout(self.meta_numbers_layout)
        self.meta_layout.addWidget(self.episode_description_box)

        self.season_number_combobox = QComboBox()
        self.season_number_combobox.setPlaceholderText("No Seasons")
        self.season_number_combobox.setDisabled(False)

        self.episode_list = QListWidget(self)
        self.episode_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.episode_list.setDisabled(True)

        spacer = QSpacerItem(1, 15)

        top_layout = QVBoxLayout()
        bottom_layout = QVBoxLayout()
        main_layout = QVBoxLayout()

        top_layout.addLayout(self.search_bar_layout)
        top_layout.addLayout(self.meta_layout)

        bottom_layout.addWidget(self.season_number_combobox)
        bottom_layout.addWidget(self.episode_list)

        main_layout.addLayout(top_layout, 1)
        main_layout.addSpacerItem(spacer)
        main_layout.addLayout(bottom_layout, 1)
        self.setLayout(main_layout)

    def get_series(self):
        """Get the displayed series name"""
        return self.series_name_box.text().strip()

    def get_series_year(self):
        """Get the displayed year"""
        return self.year_box.text().strip()

    def get_episode_title(self):
        """Get the displayed episode title"""
        return self.episode_title_box.text().strip()

    def get_season_number(self):
        """Get the displayed season number"""
        return self.season_number_box.text().strip()

    def get_episode_number(self):
        """Get the displayed episode number"""
        return self.episode_number_box.text().strip()

    def get_episode_range_number(self):
        """Get the displayed episode range number"""
        return self.episode_range_box.text().strip()

    def get_episode_part_number(self):
        """Get the displayed part number"""
        return self.part_number_box.text().strip()

    def get_episode_description(self):
        """Get the displayed episode description"""
        return self.episode_description_box.toPlainText().strip()

    def select_next_episode(self):
        """Select next episode after the selected episode in the episode list"""
        current_row = self.episode_list.currentRow()
        next_row = current_row + 1
        if next_row < self.episode_list.count():
            self.episode_list.setCurrentRow(next_row)

    def clear_seasons(self):
        """Clear the seasons combobox"""
        self.season_number_combobox.clear()
        self.season_number_combobox.setDisabled(True)

    def clear_episodes(self):
        """Clear the episode list"""
        self.episode_list.clear()
        self.episode_list.setDisabled(True)

    def clear_metadata(self):
        """Clear the displayed metadata"""
        self.series_name_box.clear()
        self.year_box.clear()
        self.episode_title_box.clear()
        self.season_number_box.clear()
        self.episode_number_box.clear()
        self.episode_range_box.clear()
        self.part_number_box.clear()
        self.episode_description_box.clear()

    def clear_query(self):
        self.search_field.clear()
