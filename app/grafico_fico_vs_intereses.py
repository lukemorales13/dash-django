import pandas as pd
import plotly.graph_objects as go

def generar_grafico_fico_vs_interes(filtros, collection):
    """
    Recibe un diccionario con los filtros:
    {
        'region': [...],
        'tipo_propiedad': [...],
        'duracion': [...]
    }
    Devuelve una figura de plotly
    """

    consulta = {}
    if 'region' in filtros and filtros['region']:
        consulta['estado_completo'] = {'$in': filtros['region']}
    if 'tipo_propiedad' in filtros and filtros['tipo_propiedad']:
        consulta['tipo_propiedad'] = {'$in': filtros['tipo_propiedad']}
    if 'duracion' in filtros and filtros['duracion']:
        duraciones = [d.strip() + " meses" if "meses" not in d else d.strip() for d in filtros['duracion']]
        consulta['duracion_prestamo'] = {'$in': duraciones}

    pipeline = [
        {'$match': consulta},
        {'$group': {
            '_id': '$mes_anio',
            'tasa_interes_promedio': {'$avg': '$tasa_interes'},
            'puntaje_fico_promedio': {'$avg': '$puntaje_fico_promedio'},
            'conteo': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}},
        {'$project': {
            '_id': 0,
            'mes_anio': '$_id',
            'tasa_interes_promedio': 1,
            'puntaje_fico_promedio': 1,
            'conteo': 1
        }}
    ]

    datos = list(collection.aggregate(pipeline))
    if not datos:
        return go.Figure()

    df = pd.DataFrame(datos)
    df['mes_anio'] = pd.to_datetime(df['mes_anio'])

    figura = go.Figure()

    figura.add_trace(go.Scatter(
        x=df['mes_anio'],
        y=df['tasa_interes_promedio'],
        name="Tasa de Interés (%)",
        line=dict(color='#3498db', width=2.5),
        yaxis='y1',
        hovertemplate='%{y:.2f}',
        text=df['conteo']
    ))

    figura.add_trace(go.Scatter(
        x=df['mes_anio'],
        y=df['puntaje_fico_promedio'],
        name="Puntaje FICO",
        line=dict(color='#e74c3c', width=2.5),
        yaxis='y2',
        hovertemplate='%{y:.0f}<br>Préstamos: %{text}',
        text=df['conteo']
    ))

    figura.update_layout(
        title=dict(text='Relación entre Tasa de Interés y Puntaje FICO', x=0.5),
        xaxis=dict(title=' ', gridcolor='#ecf0f1', showline=True, linecolor='#7f8c8d'),
        yaxis=dict(
            title=dict(text='Tasa de Interés (%)', font=dict(color='#3498db')),
            tickfont=dict(color='#3498db'),
            gridcolor='#ecf0f1',
            range=[max(0, df['tasa_interes_promedio'].min() - 2), df['tasa_interes_promedio'].max() + 2]
        ),
        yaxis2=dict(
            title=dict(text='FICO Score', font=dict(color='#e74c3c')),
            tickfont=dict(color='#e74c3c'),
            overlaying='y',
            side='right',
            range=[max(300, df['puntaje_fico_promedio'].min() - 20), min(850, df['puntaje_fico_promedio'].max() + 20)]
        ),
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.7)'),
        hovermode='x unified',
        plot_bgcolor='white',
        margin=dict(l=70, r=70, t=90, b=70),
        height=400,
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial")
    )

    return figura
