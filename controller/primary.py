from pathlib import Path
from view.video_tree import VideoTree
from view.metadata_preview import MetadataPreview
from view.video_preview import VideoPreview
from view.selection_dialog import SelectionDialog
from view.loading_dialog import LoadingDialog
from model.metadata import Series, Season, Episode
from model.tmdb import MetadataDownloader as TMDBDownloader
from model.tvdb import MetadataDownloader as TVDBDownloader
from controller.dialog import DialogController
from backend.mkvtoolnix import get_metadata_title, set_metadata_title
from PyQt6.QtWidgets import QDialog, QListWidgetItem, QFileDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEventLoop


class SearchWorker(QThread):
    search_finished = pyqtSignal(list)

    def __init__(self, downloaders, search_query):
        super().__init__()
        self.downloaders = downloaders
        self.search_query = search_query

    def run(self):
        search_results = []
        if self.search_query:
            for downloader in self.downloaders:
                search_results += downloader.search_series(self.search_query)
        self.search_finished.emit(search_results)


class PrimaryController:
    def __init__(
        self,
        video_tree: VideoTree,
        video_preview: VideoPreview,
        metadata_preview: MetadataPreview,
        parent=None,
    ):
        self.parent = parent

        self.series = None
        self.series_list = []

        self.video_tree: VideoTree = video_tree
        self.video_preview: VideoPreview = video_preview
        self.metadata_preview: MetadataPreview = metadata_preview

        self.downloaders = [TMDBDownloader(), TVDBDownloader()]
        self.loading_dialog = LoadingDialog()

        # clicking on video item will pause video
        # changing selected video will run video_selection_changed function
        self.video_tree.set_root_button.clicked.connect(self.video_preview.pause)
        self.video_tree.tree.selectionModel().selectionChanged.connect(
            self._video_selection_changed
        )

        # click on search button to run _open_search_dialog
        # press enter on search field to run _open_search_dialog
        self.metadata_preview.search_field.returnPressed.connect(
            self._open_search_dialog
        )
        self.metadata_preview.search_button.clicked.connect(self._open_search_dialog)

        # click on season in season combo box
        self.metadata_preview.season_number_combobox.currentIndexChanged.connect(
            self._season_selection_changed
        )

        # click on episode to load metadata
        self.metadata_preview.episode_list.clicked.connect(self._selected_episode_item)

        # change episode selection to load metadata
        selection_model = self.metadata_preview.episode_list.selectionModel()
        selection_model.selectionChanged.connect(self._episode_selection_changed)
        self.video_tree.set_root_button.clicked.connect(self._open_video_directory)

        # Focus query field on startup
        self.metadata_preview.search_field.setFocus()

    def _start_search_series_metadata(self, callback) -> list[Series]:
        search_query = self.metadata_preview.search_field.text().strip()
        self.worker = SearchWorker(self.downloaders, search_query)
        self.worker.search_finished.connect(self._on_search_finished)
        if callback:
            self.worker.search_finished.connect(callback)
        self.worker.start()
        self.loading_dialog.set_text("Searching...")
        self.loading_dialog.show()
        self.parent.setDisabled(True)

    def _search_series_metadata(self):
        loop = QEventLoop()
        self._start_search_series_metadata(callback=loop.quit)
        loop.exec()

    def _on_search_finished(self, search_results):
        self.series_list = search_results
        self.loading_dialog.hide()
        self.parent.setEnabled(True)

    def _open_video_directory(self):
        directory = QFileDialog.getExistingDirectory(
            None,
            "Open Folder",
            "",
        )
        self.video_tree._set_root_path(Path(directory))

    def _open_search_dialog(self) -> None:
        # Get list of series
        if self.metadata_preview.search_field.text().strip():
            self._search_series_metadata()

        # Get new series chosen by user
        dialog = SelectionDialog()
        DialogController(dialog, self.series_list)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.series = dialog.get_selected_data()

        # If a series was selected, populate GUI and clear query.
        if self.series:
            self._populate_metadata_fields()
            self.metadata_preview.clear_query()

    def _populate_season_combo_box(self):
        # Clear existing data
        self.metadata_preview.clear_seasons()

        if not self.series:
            return

        if not self.series.seasons:
            return

        # Populate season_number_combobox with new data
        for season_number in self.series.seasons:
            display_text = f"Season {season_number:02}"
            self.metadata_preview.season_number_combobox.addItem(display_text)
            self.metadata_preview.season_number_combobox.setItemData(
                self.metadata_preview.season_number_combobox.count() - 1, season_number
            )

        if not self.metadata_preview.season_number_combobox.count():
            return

        # Select first index and enable
        self.metadata_preview.season_number_combobox.setCurrentIndex(0)
        self.metadata_preview.season_number_combobox.setEnabled(True)

        # Set Season 1 (if it exists)
        index = self.metadata_preview.season_number_combobox.findData(1)
        if index >= 0:
            self.metadata_preview.season_number_combobox.setCurrentIndex(index)

        # Ensure combobox is enabled
        self.metadata_preview.season_number_combobox.setEnabled(True)

    def _populate_episode_list(self, season_number):
        # Clear previous episode list
        self.metadata_preview.clear_episodes()

        # Get season
        season = self.series.get_season(season_number)
        if not season:
            return

        # Check for at least 1 episode
        if not season.episodes:
            return

        # Populate episode list
        for number in season.episodes:
            episode = season.episodes[number]
            self._add_episode(episode)

        # Set first item as the selected episode
        self.metadata_preview.episode_list.setCurrentRow(0)
        self._populate_episode_metadata()

        # Ensure episode list is enabled
        self.metadata_preview.episode_list.setEnabled(True)

    def _populate_episode_metadata(self):
        episode = self.get_selected_episode()
        if not episode:
            return

        # Populate display with metadata
        self.metadata_preview.series_name_box.setText(episode.series_name)
        self.metadata_preview.year_box.setText(str(self.series.year))
        self.metadata_preview.season_number_box.setText(
            str(episode.season_number).zfill(2)
        )
        self.metadata_preview.episode_number_box.setText(str(episode.number).zfill(2))
        self.metadata_preview.episode_title_box.setText(episode.name)
        self.metadata_preview.episode_description_box.setText(episode.overview)
        self.metadata_preview.episode_range_box.clear()
        self.metadata_preview.part_number_box.clear()

    def _populate_metadata_fields(self):
        self._populate_season_combo_box()

        season_number = self.metadata_preview.season_number_combobox.currentData()
        self._populate_episode_list(season_number)

        self._populate_episode_metadata()

    def get_selected_season(self) -> Season | None:
        number = self.metadata_preview.season_number_combobox.currentData()
        season = self.series.get_season(number)
        if season:
            return season
        return None

    def get_selected_episode(self) -> Episode | None:
        season = self.get_selected_season()

        # Get all selected episode list items
        # This should be 1 item total.
        selected = self.metadata_preview.episode_list.selectedItems()
        if not selected:
            return

        # Get the data (episode number) for first item and return the episode
        number: int = selected[0].data(Qt.ItemDataRole.UserRole)
        episode = season.get_episode(number)
        if episode:
            return episode
        return None

    def _selected_episode_item(self):
        selected_items = self.metadata_preview.episode_list.selectedItems()
        if selected_items:
            self._populate_episode_metadata()

    def _season_selection_changed(self):
        season_number = self.metadata_preview.season_number_combobox.currentData()
        self._populate_episode_list(season_number)
        self.metadata_preview.episode_list.setFocus()

    def _episode_selection_changed(self):
        self._selected_episode_item()

    def _get_selected_video(self):
        selected_indexes = self.video_tree.tree.selectedIndexes()
        if not selected_indexes:
            return None
        index = selected_indexes[0]
        file_path = self.video_tree.model.filePath(index)
        return Path(file_path)

    def _video_selection_changed(self):
        video = self._get_selected_video()

        if video.suffix in [".mkv"]:
            # Pause playing video
            if self.video_preview._player.isPlaying():
                self.video_preview.pause()

            # Play new video
            self.video_preview.load(video.as_posix())
            self.video_preview.play()

    def _add_episode(self, episode) -> None:
        text = "S{}E{} - {}".format(
            str(episode.season_number).zfill(2),
            str(episode.number).zfill(2),
            episode.name,
        )
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, episode.number)
        self.metadata_preview.episode_list.addItem(item)

    def rename_video(self):
        loop = QEventLoop()
        self._start_rename_video(callback=loop.quit)
        loop.exec()

    def _start_rename_video(self, callback=None):
        if callback:
            self.worker.search_finished.connect(callback)

        video = self._get_selected_video()

        if not video:
            return

        if not self.series:
            return

        if not video.is_file():
            return

        series_name = self.metadata_preview.get_series()
        year = self.metadata_preview.get_series_year()
        season_number = self.metadata_preview.get_season_number()
        episode_number = self.metadata_preview.get_episode_number()
        episode_range_number = self.metadata_preview.get_episode_range_number()
        part_number = self.metadata_preview.get_episode_part_number()

        if not series_name or len(year) != 4:
            return

        for x in [year, season_number, episode_number]:
            if not x.isdecimal():
                return

        new_name = f"{series_name} ({year})"
        new_name += f" S{season_number:0>2}"
        new_name += f"E{episode_number:0>2}"

        # These two parts should be optionally added if defined
        if episode_range_number.isdecimal():
            new_name += f"-E{episode_range_number:0>2}"

        if part_number.isdecimal():
            new_name += f" Part {part_number:0>2}"

        new_name += f"{video.suffix}"
        new_video = video.parent.joinpath(new_name)

        if not new_video.exists():
            try:
                self.parent.setDisabled(True)
                self.video_preview.pause()
                self.loading_dialog.set_text("Renaming file...")
                self.loading_dialog.show()

                video = video.rename(new_video)

                title_string = self.metadata_preview.get_episode_title()
                if title_string != get_metadata_title(video):
                    set_metadata_title(title_string, video)

                self.metadata_preview.episode_range_box.clear()
                self.metadata_preview.part_number_box.clear()

                self.metadata_preview.select_next_episode()
                self.video_tree.refresh()

                self.loading_dialog.hide()
                self.parent.setEnabled(True)
            except PermissionError:
                print("Permission Error!")
