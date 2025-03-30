import json
from pathlib import Path
import requests
import requests_cache
from model.metadata import Series, Network, Season, Episode


class MetadataDownloader:
    def __init__(self, keyfile: str = "TMDB_API_KEY") -> None:
        self.token = None
        self.session = None
        self.genres = {}
        self._load_token(keyfile=keyfile)

    def _load_token(self, keyfile):
        with open(keyfile) as fn:
            self.token = fn.read().strip()

    def _new_session(
        self, cache_name: str = "metadata_cache", expiration: int = 3600 * 24 * 30
    ):
        requests_cache.install_cache(
            cache_name=cache_name,
            backend="sqlite",
            expire_after=expiration,
        )
        self.session = requests.Session()

    def _get_tmdb(self, endpoint, params={}):
        url = f"https://api.themoviedb.org/3/{endpoint}"

        if not self.session:
            self._new_session()

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer {}".format(self.token),
        }
        response = self.session.get(url, headers=headers, params=params)
        return json.loads(response.text)

    def _get_tmdb_image(self, endpoint: str, image_directory: Path = Path(".")) -> None:
        url = f"https://image.tmdb.org/t/p/original{endpoint}"

        if not self.session:
            self._new_session()

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer {}".format(self.token),
        }
        image_name = Path(endpoint).name
        image = image_directory.joinpath(image_name)

        if image.is_file():
            return

        with self.session.get(url, headers=headers, stream=True) as response:
            response.raise_for_status()
            with open(image, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

    def _process_tmdb_series_results(self, results):
        series_results = []
        for result in results:
            series = Series()
            if "id" in result:
                series.ids["tmdb"] = int(result["id"])
            if "name" in result:
                series.name = result["name"]
            if "first_air_date":
                series.air_date = result["first_air_date"]
                if series.air_date:
                    series.year = series.air_date[0:4]
            if "overview" in result:
                series.overview = result["overview"]
            if "original_name" in result:
                series.original_name = result["original_name"]
            if "genre_ids" in result:
                self._get_series_genres()
                for _id in result["genre_ids"]:
                    if _id in self.genres:
                        genre = self.genres[_id]
                        if genre in series.genres:
                            series.genres += [genre]
            if "poster_path" in result:
                series.poster_path = result["poster_path"]
            series.source = "tmdb"
            series_results += [series]
        return series_results

    def search_series(
        self,
        name: str,
        year: int = None,
        adult: bool = False,
        language="en-US",
        limit=5,
    ):
        all_series = []
        endpoint = "search/tv"
        params = {"query": name, "language": language}
        if year:
            params["first_air_year_date"] = year
        if adult:
            params["include_adult"] = "true"
        content = self._get_tmdb(endpoint=endpoint, params=params)
        if "results" in content:
            results = self._process_tmdb_series_results(content["results"])
            if len(results) > limit:
                results = results[0:limit]
            for series in results:
                _id = series.ids["tmdb"]
                content = self._get_series_details(_id)
                series = self._process_tmdb_series_details(series, content)
                for season in series.seasons.keys():
                    content = self._get_series_season(_id, season)
                    series = self._process_tmdb_series_season(series, content)
                all_series += [series]
        return all_series

    def _process_tmdb_series_details(self, series: Series, details):
        if "backdrop_path" in details:
            series.backdrop_path = details["backdrop_path"]
        if "networks" in details:
            for series_network in details["networks"]:
                network = Network()
                if "id" in series_network:
                    network.id = series_network["id"]
                if "logo_path" in series_network:
                    network.logo_path = series_network["logo_path"]
                if "name" in series_network:
                    network.name = series_network["name"]
                if "origin_country" in series_network:
                    network.origin_country = series_network["origin_country"]
                series.networks += [network]
        if "seasons" in details:
            for series_season in details["seasons"]:
                season = Season()
                season.series_name = series.name
                if "season_number" in series_season:
                    season.number = series_season["season_number"]
                if season.number not in series.seasons:
                    series.seasons[season.number] = season
        return series

    def _get_series_details(self, series_id: int):
        endpoint = f"tv/{series_id}"
        return self._get_tmdb(endpoint)

    def _process_tmdb_series_season(self, series, season):
        if "season_number" in season:
            number = season["season_number"]
            series.seasons[number].number = number
            if "name" in season:
                series.seasons[number].name = season["name"]
            if "id" in season:
                series.seasons[number].ids["tmdb"] = season["id"]
            if "poster_path" in season:
                series.seasons[number].poster_path = season["poster_path"]
            if "overview" in season:
                series.seasons[number].overview = season["overview"]
            if "episodes" in season:
                for season_episode in season["episodes"]:
                    episode = Episode()
                    episode.series_name = series.name
                    if "episode_type" in season_episode:
                        episode.type = season_episode["episode_type"]
                    if "episode_number" in season_episode:
                        episode.number = season_episode["episode_number"]
                    if "id" in season_episode:
                        episode.ids["tmdb"] = season_episode["id"]
                    if "name" in season_episode:
                        episode.name = season_episode["name"]
                    if "overview" in season_episode:
                        episode.overview = season_episode["overview"]
                    if "runtime" in season_episode:
                        if season_episode["runtime"]:
                            episode.runtime = season_episode["runtime"] * 60
                    if "season_number" in season_episode:
                        episode.season_number = season_episode["season_number"]
                    if "series_id" in season_episode:
                        episode.series_id = season_episode["series_id"]
                    if "still_path" in season_episode:
                        episode.still_path = season_episode["still_path"]
                    series.seasons[number].episodes[episode.number] = episode
        return series

    def _get_series_season(self, series_id: int, season_number: int):
        endpoint = f"tv/{series_id}/season/{season_number}"
        return self._get_tmdb(endpoint)

    def _get_series_genres(self):
        genres = {}
        endpoint = "genre/tv/list"
        content = self._get_tmdb(endpoint)
        if "genres" in content:
            for genre in content["genres"]:
                _id = genre["id"]
                if _id not in genres:
                    genres[_id] = genre["name"]
        self.genres = genres
