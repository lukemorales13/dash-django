import pandas as pd
import plotly.express as px       
import plotly.graph_objects as go  
import plotly.express as px

#Funcion auxiliar que genera el filtrado
def filtro_intereses(addr_state=None, home_ownership=None, term=None, coleccion_general=None):
    # Construir etapa de filtrado

    match_conditions = {}

    # Filtro para home_ownership (acepta string o lista, con corrección de "MORTAGE" a "MORTGAGE")
    if home_ownership is not None:
        if not isinstance(home_ownership, list):
            home_ownership = [home_ownership]
        
        # Normalizar cada valor y corregir posibles errores de tipeo
        normalized_homes = [
            h.upper().replace("MORTAGE", "MORTGAGE") 
            for h in home_ownership
        ]
        
        match_conditions["home_ownership"] = {
            "$in": normalized_homes
        }
    
    # Filtro para term (acepta string o lista, maneja espacios y formatos variables)
    if term is not None:
        if not isinstance(term, list):
            term = [term]
        
        match_conditions["term"] = {
            "$in": term
            }
    
    # Filtro para addr_state (sin cambios)
    if addr_state is not None:
        if not isinstance(addr_state, list):
            addr_state = [addr_state]
        match_conditions["addr_state"] = {
            "$in": [state.upper() for state in addr_state]
        }
    
    # Construir pipeline
    pipeline = []
    
    # Añadir etapa de filtrado si hay condiciones
    if match_conditions:
        pipeline.append({"$match": match_conditions})
    
    # Resto del pipeline
    pipeline.extend([
    {
        "$project": {
            "total_rec_int": 1,
            "int_rate": {
                "$toDouble": {
                    "$trim": {  # Elimina espacios al inicio/final antes de convertir
                        "input": {
                            "$substrBytes": [
                                "$int_rate", 
                                0, 
                                {"$subtract": [{"$strLenBytes": "$int_rate"}, 1]}
                            ]
                        }
                    }
                }
            }
        }
    },
    {
        "$bucket": {
            "groupBy": "$int_rate",
            "boundaries": [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35],
            "default": "Otros",
            "output": {
                "total_rec_int_sum": {"$sum": "$total_rec_int"},
                "count": {"$sum": 1}
            }
        }
    },
    {
        "$project": {
            "rango": {
                "$cond": [
                    {"$eq": ["$_id", "Otros"]},
                    "Otros",
                    {
                        "$concat": [
                            {"$toString": "$_id"},
                            "-",
                            {"$toString": {"$add": ["$_id", 2]}},
                            "%"
                        ]
                    }
                ]
            },
            "total_rec_int": "$total_rec_int_sum",
            "_id": 0
        }
    },
    {
        "$sort": {"rango": 1}
    }
])
    # Ejecutar agregación
    result = list(coleccion_general.aggregate(pipeline))
    
    # Diagnóstico si no hay resultados
    if not result and match_conditions:
        print("\n⚠️ No se encontraron resultados con los filtros aplicados:")
        print("Filtros usados:", match_conditions)
        print("\nValores únicos en la colección:")
        print("grade:", coleccion_general.distinct("grade"))
        if home_ownership:
            print("home_ownership:", coleccion_general.distinct("home_ownership"))
        if term:
            print("term:", coleccion_general.distinct("term"))
        if addr_state:
            print("addr_state (primeros 10):", coleccion_general.distinct("addr_state")[:10])
    
    return pd.DataFrame(result)

def crear_grafica_intereses(filtros, coleccion_general):
    # Traducción de nombres de estados (en español) a códigos (en inglés)
    estado_a_codigo = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',  'Carolina del Norte': 'NC', 
        'Carolina del Sur': 'SC', 'Colorado': 'CO', 'Connecticut': 'CT', 'Dakota del Norte': 'ND', 'Dakota del Sur': 'SD', 
        'Delaware': 'DE', 'Distrito de Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawái': 'HI', 'Idaho': 'ID', 
        'Illinois': 'IL', 'Indiana': 'IN', 'Kansas': 'KS', 'Kentucky': 'KY', 'Luisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Minnesota': 'MN', 'Misisipi': 'MS', 'Misuri': 'MO', 'Montana': 'MT', 'Míchigan': 'MI',
        'Nebraska': 'NE', 'Nevada': 'NV', 'Nueva Jersey': 'NJ', 'Nueva York': 'NY', 'Nuevo Hampshire': 'NH', 'Nuevo México': 'NM',
        'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregón': 'OR', 'Pensilvania': 'PA', 'Rhode Island': 'RI', 'Tennessee': 'TN',
        'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Virginia Occidental': 'WV', 'Washington': 'WA',
        'Wisconsin': 'WI', 'Wyoming': 'WY'
    }

    # Traducción de home_ownership (en español) a valores en inglés usados en BD
    home_ownership_traduccion = {
        'ANY': 'ANY',  
        'Hipoteca': 'MORTGAGE',
        'Alquilada': 'RENT',
        'Propia': 'OWN'
    }

    # Traducción de términos de tiempo
    term_traduccion = {
        '36 meses': ' 36 months',
        '60 meses': ' 60 months'
    }


    addr_state = [estado_a_codigo[x] for x in filtros['region']]
    home_ownership = [home_ownership_traduccion[x] for x in filtros['tipo_propiedad']]
    term = [term_traduccion[x] for x in filtros['duracion']]

    df_grouped= filtro_intereses(addr_state, home_ownership, term, coleccion_general)
    # Ordenar el dataframe por el rango (extraer el primer número para ordenar numéricamente)
    df_grouped['orden'] = df_grouped['rango'].str.split('-').str[0].str.replace('%', '').astype(float)
    df_grouped = df_grouped.sort_values('orden')
    
         # 3. Gráfico de barras (sin escala de color)
    fig = px.bar(
        df_grouped,
        x='rango',
        y='total_rec_int',
        title='Ganancias totales por rango de tasa de interés',
        labels={'rango': 'Rango de tasa (%)', 'total_rec_int': 'Ganancias totales (USD)'},
        text_auto='.2s',
        color_discrete_sequence=['#1f77b4']  # Color azul estándar
    )
    
    # 4. Añadir línea de tendencia suavizada
    fig.add_trace(go.Scatter(
        x=df_grouped['rango'],
        y=df_grouped['total_rec_int'].rolling(3, center=True).mean(),
        mode='lines',
        line=dict(color='rgba(255, 0, 0, 0.75)', width=3),  # Rojo con 50% de opacidad
        name='Tendencia'
    ))
    
    # 5. Personalización avanzada
    fig.update_layout(
        plot_bgcolor='white',
        xaxis={
        'categoryorder': 'array', 
        'categoryarray': df_grouped['rango'].tolist()  # Usar los rangos ya ordenados
        },
        hovermode='x unified',
        showlegend=True,
        legend=dict(x=0.6, y=1, bgcolor='rgba(255,255,255,0.7)')
    )
    
    fig.update_traces(
        textfont_size=12,
        textangle=0,
        textposition='outside',
        marker_line_color='black',
        marker_line_width=0.5,
        selector=({'type': 'bar'})
    )


    
    return fig
