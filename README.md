# Pet project: Movies dashboard

Live [dashboard](https://kburkin-movie-list.streamlit.app/) with movies that I have seen and personal recommendations.  
Below the table you can find curious statistics about them.

## Motivation for this project
- I want to keep detailed log of my movies 
- Receive personal recommendations of movies to watch
- Analyze what genres or directors I prefer
- Retrospect how my tastes change over time
- Share the movies I liked with my friends

## Data sources
- Initially, I used the movies list, that I kept over years. The last version of that list was published on [google spreadsheets](https://docs.google.com/spreadsheets/d/1zDdGrNWN3QnSgB_7Tj-hoDe1mEKkivMk/edit?usp=sharing&ouid=106349676610417203719&rtpof=true&sd=true) until I moved the logs here.
- I obtain additional movie credentials from [omdbapi.com](https://www.omdbapi.com/).
- For recommending system I used  [MovieLens Dataset](https://grouplens.org/datasets/movielens/) - Free dataset with millions of ratings

## Features

### 🎬 Movie Tracking
- Detailed log of watched movies with ratings and metadata
- Integration with OMDB and TMDB APIs for enriched movie data
- Interactive dashboard with statistics and analytics

### 🤖 AI-Powered Recommendations
- **Collaborative filtering** recommendation system
- Analyzes your last 6 months of viewing history
- Generates 5 personalized movie recommendations