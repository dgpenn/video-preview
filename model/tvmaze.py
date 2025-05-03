import sys
import json
import lxml.html
import requests
import requests_cache
import functools

from pathlib import Path

# Always import relative to *this* file's parent directory
sys.path.append(Path(__file__).parent.as_posix())
from metadata import Series, Network, Season, Episode, Movie


class MetadataDownloader:
    """This class is a wrapper around the TV Maze API to download metadata for series and episodes."""

    def __init__(self) -> None:
        self.session = None
        self.timeout = 60

    def _new_session(
        self, cache_name: str = "metadata_cache", expiration: int = 3600 * 24 * 30
    ):
        requests_cache.install_cache(
            cache_name=cache_name,
            backend="sqlite",
            expire_after=expiration,
        )
        self.session = requests.Session()
        self.session.request = functools.partial(
            self.session.request, timeout=self.timeout
        )

    def _get_tvmaze(self, endpoint, params={}):
        url = f"https://api.tvmaze.com/{endpoint}"

        if not self.session:
            self._new_session()

        headers = {
            "accept": "application/json",
        }
        response = self.session.get(url, headers=headers, params=params)
        raw_json = json.loads(response.text)
        return raw_json

    def search_series(
        self, name: str, year: int = None, limit: int = 5
    ) -> list[Series]:
        params = {"q": name}
        all_series = self._get_tvmaze("search/shows", params=params)
        if not all_series:
            return []
        elif len(all_series) > limit:
            all_series = all_series[0:limit]
        return self._process_series(all_series)

    def search_movies(self, name: str, year: int = None, limit: int = 5) -> list[Movie]:
        """Placeholder to search for movies. This will always return an empty list as TV Maze does not support movies."""
        return []

    def _process_externals(self, externals: dict[str, str | int]):
        """
        Process externals to extract relevant ids for other services like IMDb, TVDB, etc.
        """
        processed_externals = {}
        if "imdb" in externals:
            processed_externals["imdb"] = externals["imdb"]
        if "thetvdb" in externals:
            processed_externals["tvdb"] = externals["thetvdb"]
        if "tvmaze" in externals:
            processed_externals["tvmaze"] = externals["tvmaze"]
        if "tvrage" in externals:
            processed_externals["tvrage"] = externals["tvrage"]
        return processed_externals

    def _get_series(self, series_id: int):
        """
        Retrieve detailed information about a specific series using its ID.

        This method fetches detailed information about a series, including episodes, images, and seasons.
        This is done in one API call to minimize the number of requests.

        """
        endpoint = f"shows/{series_id}?embed[]=episodes&embed[]=images&embed[]=seasons"

        series_info = self._get_tvmaze(endpoint, params={"specials": 1})
        if not series_info:
            return None
        return series_info

    def _process_network(self, network_info: dict):
        """
        Process network information.
        """
        network = Network()

        if "name" in network_info:
            network.name = network_info["name"]
        if "id" in network_info:
            network.id = network_info["id"]
        if "country" in network_info:
            if "name" in network_info["country"]:
                network.origin_country = network_info["country"]["name"]

        return network

    def _process_html(self, html_content: str):
        if html_content:
            parsed = lxml.html.fromstring(html_content)
            return parsed.text_content().strip()
        return ""

    def _process_image(self, image: dict[str, str]):
        """
        Process the image dictionary to extract the image URL.
        """
        if image:
            if "original" in image:
                return image["original"]
            elif "medium" in image:
                return image["medium"]
        return ""

    def _process_episodes(self, series: Series, data: dict):
        for e in data["_embedded"]["episodes"]:
            episode = Episode()
            episode.series_name = series.name
            if "id" in e:
                episode.ids["tvmaze"] = e["id"]
            if "name" in e:
                episode.name = e["name"]
            if "season" in e:
                episode.season_number = e["season"]
            if "number" in e:
                episode.number = e["number"]
            if "summary" in e:
                episode.overview = self._process_html(e["summary"])
            if "runtime" in e:
                if e["runtime"]:
                    episode.runtime = int(e["runtime"]) * 60
            if "type" in e:
                episode.type = e["type"]
            if "image" in e:
                episode.still_path = self._process_image(e["image"])

            # Add the episode to the corresponding season
            # This assumes the season is already created within the series object
            if episode.season_number in series.seasons:
                series.seasons[episode.season_number].episodes[episode.number] = episode

        return series

    def _process_seasons(self, series: Series, data: dict):
        for s in data["_embedded"]["seasons"]:
            season = Season()
            season.series_name = series.name
            if "id" in s:
                season.ids["tvmaze"] = s["id"]
            if "number" in s:
                season.number = s["number"]
            if "name" in s:
                season.name = s["name"]
            if "summary" in s:
                season.overview = self._process_html(s["summary"])
            if "image" in s:
                image = s["image"]
                if image:
                    season.poster_path = self._process_image(image)

            # Ensure the season is added to the series seasons
            if season.number not in series.seasons:
                series.seasons[season.number] = season

        return series

    def _process_series(self, all_series: list[dict]) -> list[Series]:
        processed_results = []
        for result in all_series:
            series = Series()

            # Process the main show information
            series.source = "tvmaze"
            s = result["show"]
            if "id" in s:
                series.ids["tvmaze"] = s["id"]
                # Reset series with extra information in _embedded
                s = self._get_series(series_id=series.ids["tvmaze"])
            if "externals" in s:
                series.ids.update(self._process_externals(s["externals"]))
            if "name" in s:
                series.name = s["name"]
            if "summary" in s:
                if s["summary"]:
                    series.overview = self._process_html(s["summary"])
            if "premiered" in s:
                series.air_date = s["premiered"]
                if series.air_date:
                    series.year = int(series.air_date[0:4])
            if "genres" in s:
                series.genres = s["genres"]
            if "network" in s:
                network = s["network"]
                if network:
                    series.networks += [self._process_network(network)]
            if "image" in s:
                image = s["image"]
                if image:
                    series.poster_path = self._process_image(image)

            # Process the embedded information for seasons
            series = self._process_seasons(series, s)

            # Process the embedded information for episodes
            series = self._process_episodes(series, s)

            processed_results += [series]

        return processed_results
