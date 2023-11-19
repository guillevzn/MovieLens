import os
import sqlite3
from flask import render_template, request, jsonify, send_from_directory
from app import app
from calculate_recommendations import calculate_recommendations

# Función para conectarse a la base de datos
def connect_db():
    conn = sqlite3.connect('movies.db')
    conn.row_factory = sqlite3.Row
    return conn

# Import Web Favourite Icon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

# Route to display the main page with all genres
@app.route('/')
def index():
    # Crear una conexión a la base de datos
    conn = connect_db()
    cursor = conn.cursor()

    # Recuperar todos los géneros únicos
    cursor.execute('SELECT genres FROM movies')
    genres = set()
    for row in cursor.fetchall():
        # Exclude the "no genres listed" genre
        if row['genres'] != '(no genres listed)':
            genres.update(row['genres'].split('|'))

    top_movies_by_genre = {}

    # Obtener las 5 mejores películas por género
    for genre in genres:
        cursor.execute('SELECT * FROM movies WHERE genres LIKE ? ORDER BY score DESC LIMIT 5', ('%' + genre + '%',))
        top_movies = cursor.fetchall()
        top_movies_by_genre[genre] = top_movies

    # Cerrar la conexión a la base de datos
    conn.close()

    return render_template('index.html', genres=sorted(genres), top_movies_by_genre=top_movies_by_genre)

# Ruta que muestra películas por género
@app.route('/genre/<genre>')
def genre(genre):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM movies WHERE genres LIKE ? ORDER BY score DESC', ('%' + genre + '%',))
        movies = cursor.fetchall()
    except Exception as e:
        app.logger.error(f"Error querying movies by genre: {str(e)}")
        movies = []

    # Convertir las filas a una lista de diccionarios
    movies_list = []
    for movie in movies:
        movie_dict = dict(movie)
        if movie_dict['rating'] is not None:
            movie_dict['rating'] = round(movie_dict['rating'], 2)
        movies_list.append(movie_dict)

    for movie in movies_list:
        # Verificar si imdbId es un número válido
        if movie['imdbId'] is not None and isinstance(movie['imdbId'], int):
            # Convertir imdbId a una cadena y rellenar con ceros al principio
            movie['imdbId'] = str(movie['imdbId']).zfill(7)

    unique_years = sorted(set(movie['year'] for movie in movies if movie['year'] is not None), reverse=True)

    conn.close()
    return render_template('genre.html', movies=movies_list, genre=genre, unique_years=unique_years)

# Ruta que muestra detalles de una película
@app.route('/movie/<int:movieId>')
def movie(movieId):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Query the movie details using its ID
        cursor.execute('SELECT * FROM movies WHERE movieId = ?', (movieId,))
        movie = cursor.fetchone()
    except Exception as e:
        app.logger.error(f"Error querying movie details: {str(e)}")
        movie = None

    conn.close()

    if movie:

        movie_dict = dict(zip(movie.keys(), movie))

        # Format IMDb ID with leading zeros
        imdbId = str(movie_dict['imdbId']).zfill(7)
        movie_dict['imdbId'] = imdbId

        return render_template('movie.html', movie=movie_dict)
    else:
        app.logger.warning(f"Movie with ID {movieId} not found.")
        return render_template('movie_not_found.html')

# Ruta de búsqueda
@app.route('/search')
def search():
    query = request.args.get('query')
    if query:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM movies WHERE title LIKE ? AND score IS NOT NULL ORDER BY score DESC', ('%' + query + '%',))
        results = cursor.fetchall()
        conn.close()
    else:
        results = []
    return render_template('search.html', results=results)


# Ruta para obtener sugerencias de búsqueda (usada por JavaScript)
@app.route('/search_suggestions')
def search_suggestions():
    query = request.args.get('query')
    suggestions = []

    if query:
        conn = connect_db()
        cursor = conn.cursor()
        # Query the database to find movie titles that match the search query
        cursor.execute('SELECT movieId, title, year, imdbId FROM movies WHERE title LIKE ? ORDER BY score DESC', ('%' + query + '%',))
        results = cursor.fetchall()
        conn.close()

        # Create a list of suggestions with movieId, title, year, and IMDb
        for result in results:
            movie_id, title, year, imdb_id = result
            suggestions.append({'movieId': movie_id, 'title': title, 'year': year, 'imdbId': str(imdb_id).zfill(7)})

    return jsonify({'suggestions': suggestions})

@app.route('/filter_movies', methods=['GET'])
def filter_movies():
    selected_year = request.args.get('year')
    selected_rating = request.args.get('rating')

    conn = connect_db()
    cursor = conn.cursor()

    # Construye una consulta SQL para obtener películas filtradas
    query = 'SELECT * FROM movies WHERE 1 = 1'  # Inicia la consulta

    if selected_year != 'all':
        query += f' AND year = {selected_year}'  # Filtra por año

    if selected_rating != 'all':
        query += f' AND rating >= {int(selected_rating)}'  # Filtra por calificación (rating)

    cursor.execute(query)
    filtered_movies = cursor.fetchall()
    conn.close()

    # Convierte las películas en una lista de diccionarios
    movies_list = [dict(movie) for movie in filtered_movies]

    return jsonify(movies_list)

@app.route('/generate_recommendations', methods=['POST'])
def get_recommendations():
    conn = connect_db()
    cursor = conn.cursor()

    user_input = request.form.getlist('selected_movies[]')  # Obtiene las películas seleccionadas por el usuario

    # A continuación, puedes calcular las recomendaciones basadas en las puntuaciones (score)
    query = calculate_recommendations(user_input)

    cursor.execute(query)
    recommendations = cursor.fetchall()
    conn.close()

    recommendations = [{'movieId': row[0], 'title': row[1], 'year': row[2], 'score': row[3]} for row in recommendations]
    print(recommendations)

    return jsonify({'recommendations': recommendations})
