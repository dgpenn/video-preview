import sys
import json
import requests
import requests_cache
from pathlib import Path

import functools

# Always import relative to *this* file's parent directory
sys.path.append(Path(__file__).parent.as_posix())
from metadata import Artwork, SeriesArtwork, MovieArtwork


class MetadataDownloader:
    def __init__(
        self,
        project_keyfile: str = "FANARTTV_PROJECT_API_KEY",
        keyfile: str = "FANARTTV_API_KEY",
    ) -> None:
        self.client_key = None
        self.project_key = None
        self.session = None
        self.genres = {}
        self.timeout = 60
        self._load_apikey(project_keyfile, keyfile)

    def _load_apikey(self, project_keyfile, keyfile):
        with open(keyfile) as fn:
            self.client_key = fn.read().strip()

        with open(project_keyfile) as fn:
            self.project_key = fn.read().strip()

    def _normalize_type(self, type: str) -> str:
        match type:
            case "hdtvlogo" | "hdmovielogo" | "movielogo":
                return "clearlogo"
            case "hdclearart" | "hdmovieclearart" | "movieart":
                return "clearart"
            case "showbackground" | "moviebackground":
                return "fanart"
            case "tvposter" | "seasonposter" | "movieposter":
                return "poster"
            case "tvbanner" | "seasonbanner" | "moviebanner":
                return "banner"
            case "tvthumb" | "seasonthumb" | "moviethumb":
                return "landscape"
            case _:
                return type

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

    def _get_fanart(self, endpoint, params={}):
        url = f"http://webservice.fanart.tv/v3/{endpoint}"

        if not self.session:
            self._new_session()

        headers = {
            "accept": "application/json",
        }
        params["client_key"] = self.client_key
        params["api_key"] = self.project_key

        response = self.session.get(url, headers=headers, params=params)

        return json.loads(response.text)

    def _get_fanart_series(self, series_id: int | str):
        endpoint = f"tv/{series_id}"
        return self._get_fanart(endpoint)

    def _get_fanart_movie(self, movie_id: int | str):
        endpoint = f"movies/{movie_id}"
        return self._get_fanart(endpoint)

    def get_series(self, tvdb_series_id: int | str):
        results = self._get_fanart_series(tvdb_series_id)
        series_artwork = SeriesArtwork()

        if "thetvdb_id" in results:
            series_artwork.ids["tvdb"] = results["thetvdb_id"]

        for artwork_type in [
            "hdtvlogo",
            "hdclearart",
            "clearlogo",
            "clearart",
            "showbackground",
            "tvposter",
            "tvbanner",
            "tvthumb",
            "seasonposter",
            "seasonbanner",
            "seasonthumb",
            "characterart",
        ]:
            if artwork_type in results:
                for art_item in results[artwork_type]:
                    # Populate artwork item
                    artwork = Artwork()
                    artwork.type = self._normalize_type(artwork_type)
                    artwork.ids["fanarttv"] = art_item.get("id", "")
                    artwork.url = art_item.get("url", "")
                    artwork.language = art_item.get("lang", "")

                    # Skip invalid artwork
                    if not artwork.is_valid():
                        continue

                    # Add artwork as season artwork if season is specific
                    if "season" in art_item:
                        if art_item["season"] == "all":
                            series_artwork.add(artwork)
                        else:
                            season_number = art_item["season"]
                            # Reset season_number for specials
                            if "special" in str(season_number):
                                season_number = 0
                            season_number = int(season_number)
                            series_artwork.add_season_art(season_number, artwork)
                    else:
                        series_artwork.add(artwork)
        return series_artwork

    def get_movie(self, tmdb_movie_id: int | str):
        results = self._get_fanart_movie(tmdb_movie_id)
        movie_artwork = MovieArtwork()

        if "tmdb_id" in results:
            if results["tmdb_id"]:
                movie_artwork.ids["tmdb"] = results["tmdb_id"]

        if "imdb_id" in results:
            if results["imdb_id"]:
                movie_artwork.ids["imdb"] = results["imdb_id"]

        for artwork_type in [
            "hdmovielogo",
            "movielogo",
            "hdmovieclearart",
            "movieart",
            "moviedisc",
            "moviebackground",
            "movieposter",
            "moviebanner",
            "moviethumb",
        ]:
            if artwork_type in results:
                for art_item in results[artwork_type]:
                    # Populate artwork item
                    artwork = Artwork()
                    artwork.type = self._normalize_type(artwork_type)
                    artwork.ids["fanarttv"] = art_item.get("id", "")
                    artwork.url = art_item.get("url", "")
                    artwork.language = art_item.get("lang", "")

                    # Skip invalid artwork
                    if not artwork.is_valid():
                        continue

                    movie_artwork.add(artwork)
        return movie_artwork


if __name__ == "__main__":
    d = MetadataDownloader()
    art = d.get_movie(357400)
    for x in art.artwork:
        print(art.artwork[x])
