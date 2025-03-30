import json
import requests
import requests_cache
from model.metadata import Series, Network, Season, Episode


class MetadataDownloader:
    """This class is a wrapper around the TVDB API to download metadata for series and episodes."""

    def __init__(self, keyfile="TVDB_API_KEY") -> None:
        self.token = None
        self.session = None
        self.genres = {}
        self._load_token(keyfile=keyfile)

    def _new_session(
        self, cache_name: str = "metadata_cache", expiration: int = 3600 * 24 * 30
    ):
        requests_cache.install_cache(
            cache_name=cache_name,
            backend="sqlite",
            expire_after=expiration,
        )
        self.session = requests.Session()

    def _load_token(self, keyfile) -> None:
        with open(keyfile) as fn:
            apikey = fn.read().strip()

        if not apikey:
            return

        if not self.session:
            self._new_session()

        endpoint = "login"
        login_url = f"https://api4.thetvdb.com/v4/{endpoint}"
        headers = {"Content-Type": "application/json"}
        login_info = json.dumps({"apikey": apikey}).encode("utf-8")
        with self.session.post(
            url=login_url, headers=headers, data=login_info
        ) as response:
            raw_content = response.content
            content = json.loads(raw_content)
            self.token = content["data"]["token"]

    def _get_tvdb(self, endpoint, params={}):
        url = f"https://api4.thetvdb.com/v4/{endpoint}"

        if not self.session:
            self._new_session()

        if not self.token:
            self._load_token()

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer {}".format(self.token),
        }
        response = self.session.get(url, headers=headers, params=params)
        raw_json = json.loads(response.text)
        if "data" in raw_json:
            data = raw_json["data"]
            if data:
                return data
        return {}

    def search_series(
        self, name: str, year: int = None, language: str = "eng", limit: int = 5
    ) -> list[Series]:
        params = {"query": name, "language": language, "limit": limit}
        if year:
            params["year"] = year
        all_series = self._get_tvdb("search", params=params)
        if not all_series:
            return []
        return self._process_series(all_series, language=language)

    def _get_series_extended(self, series_id: int) -> dict:
        endpoint = f"series/{series_id}/extended"
        return self._get_tvdb(endpoint)

    def _get_series_translations(self, series_id: int, language: str) -> dict:
        endpoint = f"series/{series_id}/translations/{language}"
        return self._get_tvdb(endpoint)

    def _get_season(self, season_id: int) -> dict:
        endpoint = f"seasons/{season_id}"
        return self._get_tvdb(endpoint)

    def _get_series_episodes(
        self, series_id: int, season_type: str = "official", lang: str = "eng"
    ) -> dict:
        endpoint = f"series/{series_id}/episodes/{season_type}/{lang}"
        return self._get_tvdb(endpoint)

    def _process_series(
        self,
        all_series: list[dict],
        language: str = "eng",
        season_type: str = "official",
    ) -> list[Series]:
        all_shows = []
        for s in all_series:
            series = Series()
            series.ids["tvdb"] = s["tvdb_id"]
            series_extended = self._get_series_extended(series.ids["tvdb"])
            series_translation = self._get_series_translations(
                series.ids["tvdb"], language=language
            )

            if "name" in series_translation:
                series.name = series_translation["name"]
            if "name" in s:
                series.original_name = s["name"]

            if "artworks" in series_extended:
                for artwork in series_extended["artworks"]:
                    match artwork["type"]:
                        case 1:  # Series Banner
                            if not series.backdrop_path:
                                series.backdrop_path = artwork["image"]
                        case 2:  # Series Poster
                            if not series.poster_path:
                                series.poster_path = artwork["image"]

            if "genres" in series_extended:
                for genre in series_extended["genres"]:
                    series.genres += [genre]

            if "overview" in series_translation:
                series.overview = series_translation["overview"]

            if "first_air_time" in s:
                series.air_date = s["first_air_time"]

            if "year" in s:
                series.year = int(s["year"])

            if "network" in s:
                network = Network()
                network.name = s["network"]
                series.networks += [network]

            if "seasons" in series_extended:
                for series_season in series_extended["seasons"]:
                    if "type" in series_season:
                        if "type" == "offical":
                            break

                    season = Season()

                    if "id" in series_season:
                        season.ids["tvdb"] = series_season["id"]

                    tvdb_season = self._get_season(season.ids["tvdb"])
                    if tvdb_season["type"]["type"] != season_type:
                        continue

                    if "number" in tvdb_season:
                        season.number = series_season["number"]
                    if "image" in tvdb_season:
                        season.poster_path = series_season["image"]

                    season.series_name = series.name

                    if season.number not in series.seasons:
                        series.seasons[season.number] = season
                    # Season will not be valid until after episodes are processed
            series.source = "tvdb"
            series = self._process_episodes(series, season_type=season_type)

            # Empty seasons are possible, so remove them if they exist
            keys_to_remove = []
            for key in series.seasons:
                if not series.seasons[key].episodes:
                    keys_to_remove += [key]
            for key in keys_to_remove:
                series.seasons.pop(key)

            if series.is_valid():
                all_shows += [series]

        return all_shows

    def _process_episodes(
        self, series: Series, season_type: str = "official", lang: str = "eng"
    ) -> Series:
        """
        season_type: official, dvd, absolute, alternate, regional, altdvd, alttwo

        """

        series_episodes = self._get_series_episodes(
            series.ids["tvdb"], season_type=season_type, lang=lang
        )

        if "episodes" in series_episodes:
            for series_episode in series_episodes["episodes"]:
                episode = Episode()
                episode.ids["tvdb"] = series_episode["id"]
                episode.series_name = series.name

                if "name" in series_episode:
                    episode.name = series_episode["name"]
                if "number" in series_episode:
                    episode.number = int(series_episode["number"])
                if "seasonNumber" in series_episode:
                    episode.season_number = int(series_episode["seasonNumber"])
                if "overview" in series_episode:
                    episode.overview = series_episode["overview"]
                if "runtime" in series_episode:
                    if series_episode["runtime"]:
                        episode.runtime = int(series_episode["runtime"]) * 60
                if "seriesId" in series_episode:
                    episode.series_id = series_episode["seriesId"]
                if "image" in series_episode:
                    episode.still_path = series_episode["image"]
                if "finaleType" in series_episode:
                    episode.type = series_episode["finaleType"]

                if episode.season_number in series.seasons:
                    if (
                        episode.number
                        not in series.seasons[episode.season_number].episodes
                    ):
                        if episode.is_valid():
                            series.seasons[episode.season_number].episodes[
                                episode.number
                            ] = episode
        return series
