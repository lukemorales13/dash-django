import pandas as pd

import plotly.graph_objects as go

import pandas as pd
import plotly.graph_objects as go

import pandas as pd
import plotly.graph_objects as go

def grafico_ingresos_por_grado(filtros, coleccion):
    """
    Genera una figura de Plotly para ingreso promedio por grado crediticio, aplicando filtros dinámicos.
    """

    # Construir consulta en base a los filtros
    consulta = {}
    if filtros.get("region"):
        consulta["region"] = {"$in": filtros["region"]}
    if filtros.get("tipo_propiedad"):
        consulta["tipo_propiedad"] = {"$in": filtros["tipo_propiedad"]}
    if filtros.get("duracion"):
        consulta["duracion"] = {"$in": filtros["duracion"]}

    # Pipeline de agregación en MongoDB
    pipeline = [
        {'$match': consulta},
        {'$group': {
            '_id': '$grado_crediticio',
            'ingreso_promedio': {'$avg': '$ingreso_promedio'},
            'conteo_prestamos': {'$sum': '$conteo_prestamos'}
        }},
        {'$sort': {'_id': 1}},
        {'$project': {
            '_id': 0,
            'grado_crediticio': '$_id',
            'ingreso_promedio': 1,
            'conteo_prestamos': 1
        }}
    ]

    # Ejecutar agregación
    datos = list(coleccion.aggregate(pipeline))
    df = pd.DataFrame(datos)

    # Si no hay datos, retornar figura vacía
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Sin datos disponibles para los filtros seleccionados",
            template="plotly_white"
        )
        return fig

    # Crear figura de barras
    fig = go.Figure(
        data=[
            go.Bar(
                x=df["grado_crediticio"],
                y=df["conteo_prestamos"],
                text=df["conteo_prestamos"],
                textposition='auto',
                marker_color="mediumseagreen"
            )
        ],
        layout=go.Layout(
            title="Número de Préstamos por Grado Crediticio",
            xaxis_title="Grado Crediticio",
            yaxis_title="Préstamos",
            template="plotly_white"
        )
    )

    return fig
