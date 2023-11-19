import sqlite3
import pandas as pd

# Specify the name of the SQLite database file
database_name = 'movies.db'

# Create a SQLite database connection
conn = sqlite3.connect(database_name)

# Read 'movies' and 'ratings' from CSV files
movies = pd.read_csv('movielens-data/movies.csv')
ratings = pd.read_csv('movielens-data/ratings.csv')

# Read 'tags' and 'links' from CSV files
tags = pd.read_csv('movielens-data/tags.csv')
links = pd.read_csv('movielens-data/links.csv')

# Function to extract the year from the title using regular expressions
import re
def extract_year(title):
    match = re.search(r'\((\d{4})\)', title)
    if match:
        return match.group(1)
    return None

def extract_title(title):
    match = re.search(r'^(.*?)\(\d{4}\)', title)
    if match:
        return match.group(1).strip()
    return None

# Calculate mean ratings
mean_ratings = ratings.groupby('movieId')['rating'].mean().reset_index()

# Merge 'movies' and 'mean_ratings' DataFrames
movies_with_ratings = pd.merge(movies, mean_ratings, on='movieId', how='left')

# Merge 'tags' into a single string for each movie
tags_concatenated = tags.groupby('movieId')['tag'].apply(lambda x: '|'.join(str(tag) for tag in x)).reset_index()

# Merge 'tags_concatenated' into 'movies_with_ratings' on 'movieId'
movies_with_ratings = pd.merge(movies_with_ratings, tags_concatenated, on='movieId', how='left')

# Merge 'movies_with_ratings' and 'links' on 'movieId'
movies_with_ratings = pd.merge(movies_with_ratings, links, on='movieId', how='left')

# Extract the year from the title and create a new column
movies_with_ratings['year'] = movies_with_ratings['title'].apply(extract_year)

# Remove the year from the title
movies_with_ratings['title'] = movies_with_ratings['title'].apply(extract_title)

# Calcular el número de reseñas por película
reviews_per_movie = ratings.groupby('movieId')['rating'].count().reset_index()
reviews_per_movie.columns = ['movieId', 'review_count']

# Calcular la puntuación interna (internal_score) multiplicando el número de reseñas por 0.8 y la nota media por 0.2
movies_with_internal_score = pd.merge(movies_with_ratings, reviews_per_movie, on='movieId', how='left')
movies_with_internal_score['score'] = movies_with_internal_score['review_count']/max(movies_with_internal_score['review_count']) * 0.8 + movies_with_internal_score['rating']/max(movies_with_internal_score['rating']) * 0.2

# Seleccionar las columnas relevantes
movies_final = movies_with_internal_score[['movieId', 'title', 'year', 'genres', 'tag', 'rating', 'imdbId', 'review_count', 'score']]

# Conectar a la base de datos SQLite
conn = sqlite3.connect(database_name)

# Actualizar la tabla 'movies' con las nuevas columnas
movies_final.to_sql('movies', conn, if_exists='replace', index=False)


ratings['score'] = ratings['movieId'].map(movies_final.set_index('movieId')['score'])

# Actualizar la tabla 'ratings' en la base de datos
ratings.to_sql('ratings', conn, if_exists='replace', index=False)

# Confirmar los cambios y cerrar la conexión a la base de datos
conn.commit()
conn.close()

print("Las tablas 'movies' y 'ratings' han sido creadas y actualizadas con los detalles.")
