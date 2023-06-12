import fastapi
import pandas as pd
import joblib

app = fastapi.FastAPI()

df = pd.read_csv(r'df_modificado.csv')
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce', format='%Y-%m-%d')

modelo_recomendacion = joblib.load(r'modelo_joblib.joblib')

df = modelo_recomendacion['df']
vectorizer = modelo_recomendacion['vectorizer']
similarity_matrix = modelo_recomendacion['similarity_matrix']

@app.get('/cantidad_filmaciones_mes/{mes}')
def cantidad_filmaciones_mes(mes:str):
    meses=['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    mes_sel = 0
    if mes in meses:
        mes_sel = meses.index(mes) + 1
        peliculas_mes = df[df['release_date'].dt.month == mes_sel]
        cantidad_peliculas = len(peliculas_mes)   
        return {'mes':mes, 'cantidad':cantidad_peliculas}    
    else:
        return f"Mes inválido. Ingresa un nombre de mes en español válido."               

@app.get('/cantidad_filmaciones_dia{dia}')
def cantidad_filmaciones_dia(dia:str):
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    dia_sel = 0
    if dia in dias_semana:
        dia_sel = dias_semana.index(dia) + 1
        peliculas_dia = df[df['release_date'].dt.weekday == dia_sel]
        cantidad_peliculas = len(peliculas_dia)
        return {'dia':dia, 'cantidad':cantidad_peliculas}
    else:
        return {"error": "Día inválido. Ingresa un nombre de día en español válido."}

@app.get('/score_titulo/{titulo}')
def score_titulo(titulo:str):
    pelicula = df[df['title'] == titulo]
    if not pelicula.empty:
        titulo = str(pelicula['title'].values[0])
        año = int(pelicula['release_year'].values[0])
        score = float(pelicula['vote_average'].values[0])
        return {'titulo': titulo, 'anio': año, 'popularidad': score}
    else:
        return {"mensaje": "No se encontró la película en la base de datos"}
    
@app.get('/votos_titulo/{titulo}')
def votos_titulo(titulo:str):
    pelicula = df[df['title'] == titulo]
    if not pelicula.empty:
        if pelicula['vote_count'].values[0] < 2000 : 
            print('La película no cuenta con la valoracion necesaria')
        else:
            titulo= str(pelicula['title'].values[0])
            año = int(pelicula['release_year'].values[0])
            valoraciones = int(pelicula['vote_count'].values[0])
            promedio = float(pelicula['vote_average'].values[0])
            return {'titulo':titulo, 'anio':año, 'voto_total':valoraciones, 'voto_promedio':promedio}
    else:
        return f"No se encontró la película en la base de datos"
    
@app.get('/get_actor/{nombre_actor}')
def get_actor(nombre_actor:str):
    actor = df[df['cast'].apply(lambda x: nombre_actor in x)]
    if not actor.empty:
        retorno = int(actor['return'].sum())
        peliculas = int(actor.shape[0])
        retorno_promedio= float(actor['return'].mean())
        return {'actor':nombre_actor, 'cantidad_filmaciones':peliculas, 'retorno_total':retorno, 'retorno_promedio':retorno_promedio}
    else:
        return f"El actor {nombre_actor} no se encuentra en la base de datos"
    

@app.get('/get_director/{nombre_director}')
def get_director(nombre_director: str):
    director = df[df['crew'].apply(lambda x: nombre_director in x)]
    retorno_total_director = float(director['return'].sum())
    peliculas = int(director.shape[0])
    
    if not director.empty:
        peliculas_data = director[['title', 'release_year', 'return', 'budget', 'revenue']]
        peliculas_data = peliculas_data.rename(columns={'title': 'Título', 'release_year': 'Año', 'return': 'Retorno', 'budget': 'Presupuesto', 'revenue': 'Ingresos'})
        peliculas_data['Retorno'] = peliculas_data['Retorno'].round(2)
        peliculas_data = peliculas_data.head(5)
        
        respuesta = {
            'director': nombre_director,
            'retorno_total_director': retorno_total_director,
            'peliculas': peliculas,
            'peliculas_data': peliculas_data.to_dict('records')
        }
        
        return respuesta
    else:
        return f"El director {nombre_director} no se encuentra en la base de datos."
    
# ML
@app.get('/recomendacion/{titulo}')
def obtener_peliculas_similares(pelicula_consulta, n=5):
    indice_pelicula = df[df['title'] == pelicula_consulta].index[0]
    similitudes = similarity_matrix[indice_pelicula]
    indices_similares = similitudes.argsort()[::-1][1:int(n)+1]
    peliculas_similares = df.iloc[indices_similares]['title']
    return {'lista recomendada': peliculas_similares.to_list()}
