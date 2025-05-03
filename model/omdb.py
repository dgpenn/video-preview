import sys
import json
import calendar
import requests
import requests_cache
from pathlib import Path

import functools


# Always import relative to *this* file's parent directory
sys.path.append(Path(__file__).parent.as_posix())
from metadata import Series, Season, Episode, Movie


class MetadataDownloader:
    """This class is a wrapper around the OMDB API to download metadata for series and episodes."""

    def __init__(self, keyfile="OMDB_API_KEY") -> None:
        self.apikey = None
        self.session = None
        self._month_abbrs = {
            name: num for num, name in enumerate(calendar.month_abbr) if num
        }
        self.timeout = 60
        self._load_apikey(keyfile=keyfile)

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

    def _load_apikey(self, keyfile) -> None:
        with open(keyfile) as fn:
            self.apikey = fn.read().strip()

        if not self.session:
            self._new_session()

    def _get_omdb(self, params={}):
        if not self.apikey:
            self._load_apikey()

        url = "http://www.omdbapi.com/"

        if not self.session:
            self._new_session()

        headers = {
            "accept": "application/json",
        }

        params["apikey"] = self.apikey

        response = self.session.get(url, headers=headers, params=params)
        raw_json = json.loads(response.text)
        if raw_json:
            if "totalResults" in raw_json:
                if raw_json["totalResults"] == "0":
                    return {}
            if "Response" in raw_json:
                if raw_json["Response"] == "True":
                    return raw_json
        return {}

    def search_series(
        self,
        name: str,
        year: int = None,
        limit: int = 5,
        allow_missing_episodes: bool = False,
    ) -> list[Series]:
        all_series = []

        params = {"s": name, "type": "series"}
        if year:
            params["y"] = year

        results = self._get_omdb(params)
        if "Search" in results:
            if results["Search"] != "N/A":
                all_series = results["Search"]

        if len(all_series) > limit:
            all_series = all_series[0:limit]

        return self._process_series(all_series, allow_missing_episodes)

    def search_movies(
        self,
        name: str,
        year: int = None,
        limit: int = 5,
    ) -> list[Movie]:
        all_movies = []

        params = {"s": name, "type": "movie"}
        if year:
            params["y"] = year

        results = self._get_omdb(params)
        if "Search" in results:
            if results["Search"] != "N/A":
                all_movies = results["Search"]

        if len(all_movies) > limit:
            all_movies = all_movies[0:limit]

        return self._process_movies(all_movies)

    def _get_series(self, series_id):
        params = {"i": series_id, "plot": "full"}
        return self._get_omdb(params)

    def _get_movie(self, movie_id):
        params = {"i": movie_id, "plot": "full"}
        return self._get_omdb(params)

    def _get_episode(self, series_id: str, season_number: int, episode_number: int):
        params = {
            "i": series_id,
            "Season": season_number,
            "Episode": episode_number,
        }
        return self._get_omdb(params)

    def _get_season(self, series_id: str, season_number: int):
        params = {
            "i": series_id,
            "Season": season_number,
        }
        return self._get_omdb(params)

    def _process_seasons(self, series, data, allow_missing_episodes: bool = False):
        if "totalSeasons" not in data:
            return series

        if data["totalSeasons"] == "N/A":
            return series

        # Get total seasons so each can be requested
        total_seasons = int(data["totalSeasons"])

        # Process each season
        for season_number in range(1, int(total_seasons)):
            s = self._get_season(series.ids["imdb"], season_number)

            if "Season" not in s:
                continue

            if "Episodes" not in s:
                continue

            if "Season" == "N/A" or "Episodes" == "N/A":
                continue

            season = Season()
            season.series_name = series.name
            season.number = int(s["Season"])

            # This is a copy of the imdb series id because no season id exists
            # Some id must exist to pass the validity check
            season.ids["omdb"] = series.ids["imdb"]

            # Process each episode in the season
            for e in s["Episodes"]:
                episode = Episode()

                if "Episode" not in e:
                    continue

                if e["Episode"] == "N/A":
                    continue

                episode.number = int(e["Episode"])

                e = self._get_episode(series.ids["imdb"], season.number, episode.number)

                episode.series_name = series.name
                episode.season_number = season.number

                if "Title" in e:
                    if e["Title"] != "N/A":
                        episode.name = e["Title"]
                if "imdbID" in e:
                    if e["imdbID"] != "N/A":
                        episode.ids["imdb"] = e["imdbID"]
                if "Plot" in e:
                    if e["Plot"] != "N/A":
                        episode.overview = e["Plot"].replace("\\'", "'")
                if "Poster" in e:
                    if e["Poster"] != "N/A":
                        episode.still_path = e["Poster"]

                if episode.is_valid():
                    season.episodes[episode.number] = episode

            # Check if having missing episodes is allowed
            if not allow_missing_episodes:
                max_episode_number = max(season.episodes.keys())
                if len(season.episodes.keys()) < max_episode_number:
                    continue

            if season.is_valid():
                series.seasons[season.number] = season

        return series

    def _process_series(
        self, all_series: list[dict], allow_missing_episodes: bool = True
    ) -> list[Series]:
        processed_series = []
        for result in all_series:
            series = Series()
            series.source = "omdb"

            if "imdbID" not in result:
                continue

            if result["imdbID"] == "N/A":
                continue

            series.ids["imdb"] = result["imdbID"]

            s = self._get_series(series.ids["imdb"])

            if "Title" in s:
                if s["Title"] != "N/A":
                    series.name = s["Title"]
            if "Year" in s:
                if s["Year"] != "N/A":
                    series.year = int(s["Year"][0:4])
            if "Released" in s:
                if s["Released"] != "N/A":
                    release_date = s["Released"]
                    if release_date:
                        day, month, year = release_date.split()
                        series.air_date = f"{year}-{self._month_abbrs[month]}-{day}"
            if "Genre" in s:
                if s["Genre"] != "N/A":
                    genres = s["Genre"].split(",")
                    genres = [genre.strip() for genre in genres]
                    series.genres += genres
            if "Plot" in s:
                if s["Plot"] != "N/A":
                    series.overview = s["Plot"].replace("\\'", "'")
            if "Poster" in s:
                if s["Poster"] != "N/A":
                    series.poster_path = s["Poster"]

            series = self._process_seasons(series, s, allow_missing_episodes)

            if series.is_valid():
                processed_series += [series]

        return processed_series

    def _process_movies(self, all_movies: list[dict]) -> list[Movie]:
        processed_movies = []
        for result in all_movies:
            movie = Movie()
            movie.source = "omdb"

            if "imdbID" not in result:
                continue

            if result["imdbID"] == "N/A":
                continue

            movie.ids["imdb"] = result["imdbID"]

            s = self._get_movie(movie.ids["imdb"])

            if "Title" in s:
                if s["Title"] != "N/A":
                    movie.name = s["Title"]
            if "Year" in s:
                if s["Year"] != "N/A":
                    movie.year = int(s["Year"][0:4])
            if "Released" in s:
                if s["Released"] != "N/A":
                    release_date = s["Released"]
                    if release_date:
                        day, month, year = release_date.split()
                        movie.air_date = f"{year}-{self._month_abbrs[month]}-{day}"
            if "Genre" in s:
                if s["Genre"] != "N/A":
                    genres = s["Genre"].split(",")
                    genres = [genre.strip() for genre in genres]
                    movie.genres += genres
            if "Plot" in s:
                if s["Plot"] != "N/A":
                    movie.overview = s["Plot"].replace("\\'", "'")
            if "Poster" in s:
                if s["Poster"] != "N/A":
                    movie.poster_path = s["Poster"]

            if movie.is_valid():
                processed_movies += [movie]

        return processed_movies


if __name__ == "__main__":
    d = MetadataDownloader()
    movies = d.search_movies("The Matrix", limit=1)
    print(movies)
