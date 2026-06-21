"""TMDB API client for fetching movie data and building collaborative filtering dataset."""

import os
from typing import List, Dict, Optional
from tmdbv3api import TMDb, Movie, Discover
from dotenv import load_dotenv
import polars as pl
from pathlib import Path

load_dotenv()


class TMDBClient:
    """Client for interacting with The Movie Database (TMDB) API."""

    def __init__(self):
        """Initialize TMDB API client."""
        self.tmdb = TMDb()
        self.tmdb.api_key = os.getenv('TMDB_API_KEY')
        self.tmdb.language = 'en'
        self.movie = Movie()
        self.discover = Discover()

    def get_movie_by_title(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Search for a movie by title and optionally year."""
        search = self.movie.search(title)

        if not search:
            return None

        for result in search:
            if year and hasattr(result, 'release_date') and result.release_date:
                release_year = int(result.release_date.split('-')[0])
                if release_year == year:
                    return self._format_movie_details(result)
            elif not year:
                return self._format_movie_details(result)

        return self._format_movie_details(search[0]) if search else None

    def get_similar_movies(self, tmdb_id: int, limit: int = 20) -> List[Dict]:
        """Get similar movies based on TMDB's recommendation algorithm."""
        similar = self.movie.similar(tmdb_id)
        similar_list = list(similar) if similar else []
        return [self._format_movie_details(m) for m in similar_list[:limit]]

    def get_recommendations(self, tmdb_id: int, limit: int = 20) -> List[Dict]:
        """Get movie recommendations based on TMDB's algorithm."""
        recommendations = self.movie.recommendations(tmdb_id)
        recommendations_list = list(recommendations) if recommendations else []
        return [self._format_movie_details(m) for m in recommendations_list[:limit]]

    def discover_by_genres(self, genre_ids: List[int], min_rating: float = 7.0, limit: int = 20) -> List[Dict]:
        """Discover movies by genre IDs with minimum rating."""
        movies = self.discover.discover_movies({
            'with_genres': ','.join(map(str, genre_ids)),
            'vote_average.gte': min_rating,
            'vote_count.gte': 100,
            'sort_by': 'vote_average.desc'
        })
        # Convert to list to handle TMDB API object properly
        movies_list = list(movies) if movies else []
        return [self._format_movie_details(m) for m in movies_list[:limit]]

    def discover_popular_recent(self, min_year: int = 2020, limit: int = 50) -> List[Dict]:
        """Discover popular recent movies."""
        movies = self.discover.discover_movies({
            'primary_release_date.gte': f'{min_year}-01-01',
            'vote_average.gte': 7.0,
            'vote_count.gte': 200,
            'sort_by': 'popularity.desc'
        })
        # Convert to list to handle TMDB API object properly
        movies_list = list(movies) if movies else []
        return [self._format_movie_details(m) for m in movies_list[:limit]]

    def _format_movie_details(self, movie) -> Dict:
        """Format movie data into a consistent dictionary."""
        return {
            'tmdb_id': movie.id,
            'title': movie.title,
            'year': int(movie.release_date.split('-')[0]) if hasattr(movie, 'release_date') and movie.release_date else None,
            'genre_ids': movie.genre_ids if hasattr(movie, 'genre_ids') else [],
            'rating': movie.vote_average if hasattr(movie, 'vote_average') else None,
            'popularity': movie.popularity if hasattr(movie, 'popularity') else None,
            'overview': movie.overview if hasattr(movie, 'overview') else '',
            'poster_path': movie.poster_path if hasattr(movie, 'poster_path') else None,
        }

    def enrich_watched_movies_with_tmdb_ids(self, movies_df: pl.DataFrame) -> pl.DataFrame:
        """Add TMDB IDs to watched movies dataframe."""
        tmdb_ids = []

        for row in movies_df.iter_rows(named=True):
            movie_data = self.get_movie_by_title(row['title'], row.get('year'))
            tmdb_ids.append(movie_data['tmdb_id'] if movie_data else None)

        return movies_df.with_columns(
            pl.Series('tmdb_id', tmdb_ids)
        )


# TMDB Genre IDs mapping
GENRE_MAP = {
    'Action': 28,
    'Adventure': 12,
    'Animation': 16,
    'Comedy': 35,
    'Crime': 80,
    'Documentary': 99,
    'Drama': 18,
    'Family': 10751,
    'Fantasy': 14,
    'History': 36,
    'Horror': 27,
    'Music': 10402,
    'Mystery': 9648,
    'Romance': 10749,
    'Science Fiction': 878,
    'TV Movie': 10770,
    'Thriller': 53,
    'War': 10752,
    'Western': 37
}
