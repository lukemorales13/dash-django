import pandas as pd
import plotly.graph_objects as go

traduccion = {
    '60 meses': '60 months',
    '36 meses': '36 months',
    'Hipoteca': 'MORTGAGE',
    'Alquilada': 'RENT',
    'Propia': 'OWN',
    'Todas': 'ANY',
    'ANY': 'Todas'
}

def generar_grafico_ingreso_por_grado(filtross, collection):
    """
    Recibe un diccionario con filtros:
    {
        'region': [...],
        'tipo_propiedad': [...],
        'duracion': [...]
    }
    Devuelve una figura de plotly con ingreso promedio por grado de préstamo
    """
    # Copia de los filtros para evitar modificar el original
    filtros = filtross.copy()
    filtros['tipo_propiedad'] = [traduccion[x] for x in filtros['tipo_propiedad']]
    filtros['duracion'] = [traduccion[x] for x in filtros['duracion']]

    if not filtros['tipo_propiedad'] or "ANY" in filtros['tipo_propiedad']:
        filtros['tipo_propiedad'] = ['ANY', 'MORTGAGE', 'RENT', 'OWN']

    # Construcción del filtro para MongoDB
    query = {}
    if 'region' in filtros and filtros['region']:
        query['_id.estado'] = {'$in': filtros['region']}
    if 'tipo_propiedad' in filtros and filtros['tipo_propiedad']:
        query['_id.tipo_vivienda'] = {'$in': filtros['tipo_propiedad']}
    if 'duracion' in filtros and filtros['duracion']:
        query['_id.duracion'] = {'$in': filtros['duracion']}

    # Pipeline de agregación
    pipeline = [
        {'$match': query},
        {'$group': {
            '_id': '$_id.grade',
            'ingreso_promedio': {'$avg': '$ingreso_promedio'},
            'conteo_prestamos': {'$sum': '$conteo_prestamos'}
        }},
        {'$sort': {'_id': 1}},
        {'$project': {
            '_id': 0,
            'grade': '$_id',
            'ingreso_promedio': 1,
            'conteo_prestamos': 1
        }}
    ]

    datos = list(collection.aggregate(pipeline))
    if not datos:
        return go.Figure()

    df = pd.DataFrame(datos)

    # Crear figura
    figura = go.Figure()

    figura.add_trace(go.Bar(
        x=df['grade'],
        y=df['ingreso_promedio'],
        text=df['conteo_prestamos'],
        textposition='auto',
        marker_color='#3498db',
        hovertemplate='Grado: %{x}<br>Ingreso promedio: %{y:.2f}<br>Préstamos: %{text}',
        name="Ingreso Promedio"
    ))

    figura.update_layout(
        title=dict(text='Ingreso Anual Promedio<br>por Grado de Préstamo', x=0.5),
        xaxis=dict(
            title='Grado del Préstamo',
            categoryorder='array',
            categoryarray=sorted(df['grade'].dropna())
        ),
        yaxis=dict(title='Ingreso Anual Promedio (USD)'),
        plot_bgcolor='white',
        margin=dict(l=20, r=0, t=100, b=10),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
        height=400,
        width=300,
    )

    return figura
