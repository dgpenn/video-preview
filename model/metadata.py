from dataclasses import dataclass, field
from typing import ClassVar
from functools import total_ordering
from pathlib import Path
import requests
import requests_cache


@total_ordering
@dataclass
class Artwork:
    TYPES: ClassVar[list[str]] = [
        "banner",
        "characterart",
        "clearart",
        "clearlogo",
        "discart",
        "fanart",
        "fanartxx",
        "keyart",
        "landscape",
        "poster",
        "posterx",
        "thumb",
        "actor",
        "back",
        "logo",
        "spine",
        "folder",
        "backdrop",
    ]

    ids: dict = field(default_factory=dict[str, str | int])
    url: str = ""
    language: str = ""
    type: str = ""
    session: requests.Session = None

    def _new_session(
        self, cache_name: str = "metadata_cache", expiration: int = 3600 * 24 * 30
    ):
        requests_cache.install_cache(
            cache_name=cache_name,
            backend="sqlite",
            expire_after=expiration,
        )
        self.session = requests.Session()

    def is_valid(self) -> bool:
        if self.ids and self.url and self.type in Artwork.TYPES:
            return True
        return False

    def download(self, directory: Path = Path("."), filename: Path = "") -> Path:
        """Download image to the given directory.
        If filename is specified, image will be saved as that filename in the given directory.
        """

        if not self.url:
            return None

        if not filename:
            filename = Path(self.url.rsplit("/", 1)[-1])
        else:
            suffix = Path(self.url.rsplit("/", 1)[-1]).suffix
            filename = f"{Path(filename).stem}{suffix}"

        if not self.session:
            self._new_session()

        image = directory.joinpath(filename)

        if image.is_file():
            return

        with self.session.get(self.url, stream=True) as response:
            response.raise_for_status()

            with open(image, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

        return image

    def __eq__(self, other):
        if self.ids:
            for key in self.ids:
                if key in other.ids:
                    return self.ids[key] == other.ids[key]

        return False

    def __lt__(self, other):
        if self.ids:
            for key in self.ids:
                if key in other.ids:
                    return self.ids[key] < other.ids[key]
        return False


@dataclass
class ArtworkGroup:
    ids: dict = field(default_factory=dict[str, str | int])
    media_type: str = ""  # series, movie, season, episode, music
    artwork: dict = field(default_factory=dict[str, list[Artwork]])

    def add(self, artwork: Artwork):
        if not artwork.is_valid():
            return

        if artwork.type not in self.artwork:
            self.artwork[artwork.type] = []

        if artwork not in self.artwork[artwork.type]:
            self.artwork[artwork.type] += [artwork]


@dataclass
class SeriesArtwork(ArtworkGroup):
    media_type: str = "series"
    seasons = {}

    def add_season_art(self, season_number: int, artwork: Artwork):
        if not artwork.is_valid():
            return

        if season_number not in self.seasons:
            self.seasons[season_number] = ArtworkGroup()

        if artwork.type not in self.seasons[season_number].artwork:
            self.seasons[season_number].artwork[artwork.type] = []

        if artwork not in self.seasons[season_number].artwork[artwork.type]:
            self.seasons[season_number].add(artwork)

    def get_season_art(self, season_number: int, type: str = "poster") -> list[Artwork]:
        """
        Get art designated for the given season and type specified.

        Possible types are defined in Artwork.TYPES

        """
        if season_number in self.seasons:
            if type in self.seasons[season_number].artwork:
                return self.seasons[season_number].artwork[type]

        return []

    def get_series_art(self, type: str = "poster") -> list[Artwork]:
        """
        Get art designated for the given series and type specified.
        This does not include season-specific art.
        Use get_season_art instead if needed.

        Possible types are defined in Artwork.TYPES

        """
        if type in self.artwork:
            return self.artwork[type]
        return []


@dataclass
class MovieArtwork(ArtworkGroup):
    media_type: str = "movie"

    def get_movie_art(self, type: str = "poster") -> list[Artwork]:
        """
        Get art designated for the given movie and type specified.

        Possible types are defined in Artwork.TYPES

        """
        if type in self.artwork:
            return self.artwork[type]
        return []


@dataclass
class Network:
    id: int = -1
    logo_path: str = ""
    name: str = ""
    origin_country: str = ""


@dataclass
class Episode:
    ids: dict = field(default_factory=dict[str, int])
    series_id: int = -1
    number: int = -1
    season_number: int = -1
    name: str = ""
    overview: str = ""
    runtime: int = -1
    type: str = ""
    still_path: str = ""
    series_name: str = ""

    def is_valid(self) -> bool:
        if (
            self.ids
            and self.series_id
            and self.number
            and self.season_number
            and self.name
            and self.series_name
        ):
            return True
        return False

    def __repr__(self):
        return "S{}E{} - {}\n{}".format(
            str(self.season_number).zfill(2),
            str(self.number).zfill(2),
            self.name,
            self.overview,
        )


@dataclass
class Season:
    ids: dict = field(default_factory=dict[str, int])
    number: int = -1
    episodes: dict = field(default_factory=dict[int, Episode])
    name: str = ""
    series_name: str = ""
    overview: str = ""
    poster_path: str = ""

    def is_valid(self) -> bool:
        if self.ids and self.number and self.episodes and self.series_name:
            return True
        return False

    def get_episode(self, episode_number: int):
        if episode_number in self.episodes:
            episode = self.episodes[episode_number]
            return episode
        return None


@dataclass
class Series:
    ids: dict = field(default_factory=dict[str, int])
    seasons: dict = field(default_factory=dict[int, Season])
    name: str = ""
    original_name: str = ""
    overview: str = ""
    air_date: str = ""
    year: int = -1
    genres: list = field(default_factory=list[str])
    networks: list = field(default_factory=list[Network])
    poster_path: str = ""
    backdrop_path: str = ""
    source: str = ""

    def is_valid(self) -> bool:
        if self.ids and self.seasons and self.name and self.year and self.source:
            return True
        return False

    def get_season(self, season_number: int):
        if season_number in self.seasons:
            return self.seasons[season_number]
        return None

    def get_episode(self, season_number: int, episode_number: int):
        season = self.get_season(season_number)
        if not season:
            return None
        if episode_number in season.episodes:
            return season.episodes[episode_number]
        return None


@dataclass
class Movie:
    ids: dict = field(default_factory=dict[str, int])
    collection_ids: dict = field(default_factory=dict[str, int])
    collection_backdrop_path: str = ""
    collection_name: str = ""
    name: str = ""
    original_name: str = ""
    overview: str = ""
    air_date: str = ""
    year: int = -1
    genres: list = field(default_factory=list[str])
    networks: list = field(default_factory=list[Network])
    poster_path: str = ""
    backdrop_path: str = ""
    source: str = ""

    def is_valid(self) -> bool:
        if self.ids and self.name and self.year and self.source:
            return True
        return False
