#!/usr/bin/env python
from PyQt6.QtCore import Qt, QUrl, QSortFilterProxyModel
from PyQt6.QtGui import QBrush, QColor, QPainter
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
)


# class VideoFilterProxyModel(QSortFilterProxyModel):
#     def __init__(self, extensions=[".mkv"], parent=None):
#         super().__init__(parent)
#         self.extensions = extensions

#     def filterAcceptsRow(self, source_row, source_parent):
#         index = self.sourceModel().index(source_row, 0, source_parent)
#         if self.sourceModel().isDir(index):
#             return True
#         file_path = self.sourceModel().filePath(index)
#         return any(file_path.endswith(ext) for ext in self.extensions)


class VideoScrubber(QSlider):
    """A customized QSlider to act as a video scrubber."""

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            value = (
                self.minimum()
                + (self.maximum() - self.minimum())
                * event.position().x()
                / self.width()
            )
            self.setValue(int(value))
            event.accept()
        super().mousePressEvent(event)
        self.sliderMoved.emit(int(value))


class VideoPreview(QWidget):
    """A QWidget for a rudimentary video player to preview videos."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # This is a graphics item that displays video for the player
        self._video_item = QGraphicsVideoItem()
        self._video_item.nativeSizeChanged.connect(self._update_view_size)

        # This is a manager for all graphic items
        self._scene = QGraphicsScene(self)
        self._scene.addItem(self._video_item)

        # This displays the scene content
        # This can be thought of as the "background" with all other items added on top
        self._graphics_view = QGraphicsView(self._scene, self)
        self._graphics_view.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self._graphics_view.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._graphics_view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Add Player Buttons
        self._player_buttons = QHBoxLayout()

        self._play_button = QPushButton(self)
        self._play_button.setText("⏸︎")
        self._play_button.setObjectName("PlayerButton")
        self._play_button.setDisabled(True)
        self._play_button.clicked.connect(self._toggle_play)

        self._stop_button = QPushButton(self)
        self._stop_button.setText("⏹︎")
        self._stop_button.setObjectName("PlayerButton")
        self._stop_button.setDisabled(True)
        self._stop_button.clicked.connect(self.stop)

        self._toggle_mute_button = QPushButton()
        self._toggle_mute_button.setText("🔈")
        self._toggle_mute_button.setObjectName("PlayerButton")
        self._toggle_mute_button.setDisabled(True)
        self._toggle_mute_button.clicked.connect(self._toggle_mute)

        self._toggle_lock_button = QPushButton()
        self._toggle_lock_button.setText("🔒")
        self._toggle_lock_button.setObjectName("PlayerButton")
        self._toggle_lock_button.setDisabled(True)
        self._toggle_lock_button.clicked.connect(self._toggle_lock)

        self._player_buttons.addWidget(self._play_button, 1)
        self._player_buttons.addWidget(self._stop_button, 1)
        self._player_buttons.addWidget(self._toggle_mute_button, 1)
        self._player_buttons.addWidget(self._toggle_lock_button, 1)

        # The player plays and manages media content
        self._player = QMediaPlayer(self)
        self._player.setLoops(-1)  # -1: infinite, 1: once
        self._player.setAudioOutput(QAudioOutput(self))
        self._player.audioOutput().setMuted(True)
        self._player.setVideoOutput(self._video_item)
        self._player.playbackStateChanged.connect(self._on_playback_change)

        # This is the time position displayed in the video corner
        self._time_label = QLabel(self)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setObjectName("TimeLabel")

        # This is the timestamp "locked" to seek to instead of 00:00
        self.lock_position = 0
        self._lock_label = QLabel(self)
        self._lock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lock_label.setObjectName("LockLabel")
        self._update_lock_label(self.lock_position)

        # Setup Scrubber
        self._scrubber = VideoScrubber(Qt.Orientation.Horizontal, self)
        self._scrubber.setObjectName("VideoScrubber")
        self._scrubber.setDisabled(True)
        self._scrubber.sliderMoved.connect(self._update_video_position)
        self._scene.addWidget(self._scrubber)

        self._player.durationChanged.connect(self._on_duration_change)
        self._player.positionChanged.connect(self._on_video_position_change)
        self._player.mediaStatusChanged.connect(self._on_media_status_change)

        # Add everything to layout and set layout to widget
        main_layout = QVBoxLayout()
        main_layout.addLayout(self._player_buttons)
        main_layout.addWidget(self._graphics_view)
        self.setLayout(main_layout)

    def play(self):
        """Play video"""
        self._player.play()

    def stop(self):
        """Stop video"""
        self._player.stop()

    def pause(self):
        """Pause video"""
        self._player.pause()

    def _toggle_lock(self):
        """Toggle the lock position, setting the position to current position when clicked."""

        if not self.lock_position:
            self.lock_position = self._player.position()
            self._update_lock_label(self.lock_position)
            self._toggle_lock_button.setText("🔓")
        else:
            self.lock_position = 0
            self._update_lock_label(self.lock_position)
            self._toggle_lock_button.setText("🔒")

    def _toggle_mute(self):
        """Toggle mute"""

        if self._player.audioOutput().isMuted():
            self._toggle_mute_button.setText("🔇")
            self._player.audioOutput().setMuted(False)
        else:
            self._toggle_mute_button.setText("🔈")
            self._player.audioOutput().setMuted(True)

    def _toggle_play(self):
        """Toggles play to pause and vice versa."""

        if self._player.isPlaying():
            self.pause()
        else:
            self.play()

    def load(self, filename):
        """Load a new video file.

        Enable the player buttons and scrubber after loading the video.
        Plays and pauses the video on load to ensure Qt metadata is available.
        Updates graphics view size to ensure video is displayed properly.
        """

        self._player.setSource(QUrl.fromLocalFile(filename))
        self._play_button.setEnabled(True)
        self._stop_button.setEnabled(True)
        self._toggle_mute_button.setEnabled(True)
        self._toggle_lock_button.setEnabled(True)
        self._scrubber.setEnabled(True)

        # Play and pause to load metadata
        self.play()
        self.pause()
        self._update_view_size()

    def _update_scrubber_position(self, position):
        """Update the scrubber position"""
        self._scrubber.setValue(position)

    def _update_scrubber_range(self, duration):
        """Update the scrubber range"""
        self._scrubber.setRange(0, duration)

    def _update_video_position(self, position):
        """Update video position.

        This function disconnects the player's positionChanged signal.
        This avoids conflicts with on_video_position_changed.

        """
        self._player.positionChanged.disconnect()
        self._player.setPosition(position)
        self._player.positionChanged.connect(self._on_video_position_change)

    def _on_video_position_change(self, position):
        """Function to call when video position is changed.

        This updates the scrubber position and time label.
        """
        self._update_scrubber_position(position)
        self._update_time_label(position)

    def _on_media_status_change(self):
        """Function to run when the player media status changes.

        This sets the video position to the lock position.
            - The lock position needs to be set and displayed.
            - The lock position is later than the current video position.
            - The media status needs to be "BufferedMedia"
        """

        match self._player.mediaStatus().value:
            case 5:  # BufferedMedia
                if self.lock_position > self._player.position():
                    self._update_video_position(self.lock_position)

    def _on_playback_change(self):
        """Function to run on playback change

        This sets the correct play/pause symbol on state change.
        """

        if self._player.isPlaying():
            self._play_button.setText("⏸︎")
        else:
            self._play_button.setText("⏵︎")

    def _on_duration_change(self, duration):
        """Function to run on video duratioj change

        Updates the scrubber range.
        """

        self._update_scrubber_range(duration)

    def _update_view_size(self):
        """Update the view to ensure the video is displayed properly"""

        # Ensure the graphics view is the "background"
        self._graphics_view.lower()

        # Resize the video item to the actual video size
        self._video_item.setSize(self._video_item.nativeSize())

        # Resize the entire area to fit the video item
        # KeepAspectRatio will show letter-boxing / pillar-boxing
        # KeepAspectRatioExpanding will expand and crop video
        self._graphics_view.fitInView(
            self._video_item, Qt.AspectRatioMode.KeepAspectRatio
        )

        # This will ensure video is always centered
        # This matters if the video is cropped
        self._graphics_view.centerOn(self._video_item)

    def _update_time_label(self, position):
        """Update time label"""
        minutes = position // 60000
        seconds = (position % 60000) // 1000
        self._time_label.setText(f"{minutes:02}:{seconds:02}")

    def _update_time_label_position(self):
        """Update time label position"""
        graphics_view_rect = self._graphics_view.geometry()
        time_label_x = graphics_view_rect.right() - self._time_label.width() - 10
        time_label_y = graphics_view_rect.top() + 5
        self._time_label.move(time_label_x, time_label_y)

    def _update_lock_label(self, position):
        """Update lock label"""
        if position:
            minutes = position // 60000
            seconds = (position % 60000) // 1000
            self._lock_label.setEnabled(True)
            self._lock_label.setText(f"{minutes:02}:{seconds:02}")
        else:
            self._lock_label.setDisabled(True)

    def _update_lock_label_position(self):
        """Update lock label position"""
        graphics_view_rect = self._graphics_view.geometry()
        lock_label_x = graphics_view_rect.right() - self._lock_label.width() - 10
        lock_label_y = graphics_view_rect.bottom() - self._lock_label.height() - 30
        self._lock_label.move(lock_label_x, lock_label_y)

    def _update_scrubber_widget_position(self):
        """Update the scrubber position to correspond with the graphics view"""
        graphics_view_rect = self._graphics_view.geometry()
        self._scrubber.setFixedWidth(int(self._graphics_view.width() * 0.95))
        scrubber_x = graphics_view_rect.left() + int(
            (self._graphics_view.width() - self._scrubber.width()) / 2
        )
        scrubber_y = graphics_view_rect.bottom() - 30
        self._scrubber.move(scrubber_x, scrubber_y)

    def hideEvent(self, event):
        """Qt hide event.

        Pause the video when hidden.
        """
        super().hideEvent(event)
        self._player.pause()

    def showEvent(self, event):
        """Qt show event.

        Update the graphics view, scrubber, and label positions.
        """

        super().showEvent(event)
        self._update_view_size()
        self._update_time_label_position()
        self._update_lock_label_position()
        self._update_scrubber_widget_position()

    def resizeEvent(self, event):
        """Qt resize event.

        Update the graphics view, scrubber, and label positions.
        """
        super().resizeEvent(event)
        self._update_view_size()
        self._update_time_label_position()
        self._update_lock_label_position()
        self._update_scrubber_widget_position()
