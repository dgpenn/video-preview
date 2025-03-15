from dataclasses import dataclass, field


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
