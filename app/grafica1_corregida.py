import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = 'notebook'

#Funcion auxiliar que genera el filtrado
def filtro1(addr_state=None, home_ownership=None, term=None, coleccion= None):
    '''
    Función auxiliar que realiza la consulta y filtrado.

    addr_state: lista de códigos de estados válidos como ['CA','NY','TX']
    home_ownership: lista de elementos como ['MORTGAGE', 'OWN', 'RENT']
    term: lista como ['36 months', '60 months']
    '''
    pipeline = [
        # 1. Filtrar documentos con issue_d en formato correcto
        {
            "$match": {
                "issue_d": {
                    "$regex": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
                }
            }
        },
        # 2. Limpiar campos y convertir fecha
        {
            "$addFields": {
                "issue_d": {
                    "$dateFromString": {
                        "dateString": "$issue_d",
                        "format": "%Y-%m-%d %H:%M:%S"
                    }
                },
                "term_limpio": {
                    "$replaceAll": {
                        "input": "$term",
                        "find": " ",
                        "replacement": ""
                    }
                },
                "home_ownership_limpio": {
                    "$replaceAll": {
                        "input": "$home_ownership",
                        "find": " ",
                        "replacement": ""
                    }
                }
            }
        },
        # 3. Extraer fecha y mes
        {
            "$project": {
                "issue_d": 1,
                "addr_state": 1,
                "term_limpio": 1,
                "home_ownership_limpio": 1,
                "anio": {"$year": "$issue_d"},
                "mes_num": {"$month": "$issue_d"},
                "mes": {
                    "$let": {
                        "vars": {
                            "meses": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                        },
                        "in": {
                            "$arrayElemAt": [
                                "$$meses",
                                {"$subtract": [{"$month": "$issue_d"}, 1]}
                            ]
                        }
                    }
                }
            }
        }
    ]

    # 4. Aplicar filtros si se proporcionan
    filters = {}
    if addr_state is not None:
        filters["addr_state"] = {"$in": addr_state}
    if home_ownership is not None:
        filters["home_ownership_limpio"] = {"$in": [h.replace(" ", "") for h in home_ownership]}
    if term is not None:
        filters["term_limpio"] = {"$in": [t.replace(" ", "") for t in term]}

    if filters:
        pipeline.append({"$match": filters})

    # 5. Agrupamiento
    pipeline.extend([
        {
            "$group": {
                "_id": {
                    "anio": "$anio",
                    "mes": "$mes",
                    "mes_num": "$mes_num"
                },
                "prestamos": {"$sum": 1}
            }
        },
        {
            "$project": {
                "anio": "$_id.anio",
                "mes": "$_id.mes",
                "orden_mes": "$_id.mes_num",
                "prestamos": 1,
                "_id": 0
            }
        },
        {
            "$sort": {"anio": 1, "orden_mes": 1}
        }
    ])

    return pd.DataFrame(list(coleccion.aggregate(pipeline)))

def obtener_figura_1(filtros, coleccion):
    '''
    Función que regresa la figura de la gráfica como objeto Plotly.

    addr_state: lista de códigos de estados como ['CA','NY']
    home_ownership: lista como ['MORTGAGE', 'OWN']
    term: lista como ['36 months', '60 months']
    '''
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

    prestamos_agrupados = filtro1(addr_state, home_ownership, term, coleccion)

    if prestamos_agrupados.empty:
        return go.Figure()

    fig = go.Figure()

    años = prestamos_agrupados['anio'].unique()
    for anio in sorted(años):
        datos_año = prestamos_agrupados[prestamos_agrupados['anio'] == anio].sort_values('orden_mes')
        fig.add_trace(go.Scatter(
            x=datos_año['mes'],
            y=datos_año['prestamos'],
            mode='lines+markers',
            fill='tozeroy',
            name=f'Préstamos {anio}'
        ))

    fig.update_layout(
        title="Préstamos mensuales por año",
        xaxis_title="Mes",
        yaxis_title="Cantidad de préstamos",
        xaxis=dict(
            categoryorder='array',
            categoryarray=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ),
        template="plotly_white",
        legend=dict(x=0.02, y=1.13, bgcolor='rgba(255,255,255,0.7)'),
        width=300,
        margin=dict(l=20, r=0, t=100, b=10),
    )

    return fig
