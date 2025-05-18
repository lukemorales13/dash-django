import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import copy

def grafico_morosos_intereses(filtros, collection):
    # Generamos las consultas
    consulta = {}
    if 'region' in filtros and filtros['region']:
        consulta['estado_completo'] = {'$in': filtros['region']}
    if 'tipo_propiedad' in filtros and filtros['tipo_propiedad']:
        consulta['tipo_propiedad'] = {'$in': filtros['tipo_propiedad']}
    if 'duracion' in filtros and filtros['duracion']:
        duraciones = [d.strip() + " meses" if "meses" not in d else d.strip() for d in filtros['duracion']]
        consulta['duracion_prestamo'] = {'$in': duraciones}
    
    consulta_morosos = copy.deepcopy(consulta)
    consulta_morosos['loan_status'] = {
        '$in': ['Charged Off', 'Default', 'Late (31-120 days)', 'Late (16-30 days)']
    }

    # Pipeline para morosos
    pipeline_morosos = [
        {'$match': consulta_morosos}
    ]
    
    # Pipeline para totales (sin el paso de quitar el símbolo %)
    pipeline_totales = [
        {"$match": consulta},
        {
            "$project": {
                "rango": {
                    "$switch": {
                        "branches": [
                            { "case": { "$lt": ["$tasa_interes", 11] }, "then": "<11%" },
                            { "case": { "$and": [{ "$gte": ["$tasa_interes", 11] }, { "$lt": ["$tasa_interes", 16] }] }, "then": "11% - 16%" },
                            { "case": { "$and": [{ "$gte": ["$tasa_interes", 16] }, { "$lt": ["$tasa_interes", 21] }] }, "then": "16% - 21%" },
                            { "case": { "$and": [{ "$gte": ["$tasa_interes", 21] }, { "$lt": ["$tasa_interes", 26] }] }, "then": "21% - 26%" },
                            { "case": { "$gte": ["$tasa_interes", 26] }, "then": ">26%" }
                        ],
                        "default": "Desconocido"
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$rango",
                "totalPrestamos": { "$sum": 1 }
            }
        },
        {
            "$sort": { "_id": 1 }
        }
    ]
    
    # Hacemos las consultas y guardamos los resultados
    morosos = list(collection.aggregate(pipeline_morosos))
    totales = list(collection.aggregate(pipeline_totales))
    df_morosos = pd.DataFrame(morosos)
    totales_dict = {r["_id"]: r["totalPrestamos"] for r in totales}
    
    if not morosos:
        return go.Figure()

    # Dividimos los intereses en bins
    bins = [float('-inf'), 11, 16, 21, 26, float('inf')]  
    bin_labels = ['<11%', '11% - 16%', '16% - 21%', '21% - 26%', '>26%']
    df_morosos['Rango'] = pd.cut(df_morosos['tasa_interes'], bins=bins, labels=bin_labels, include_lowest=True)  
    
    # Contamos los intereses
    intereses = df_morosos['Rango'].value_counts()  
    
    # Calculamos la proporción de morosidad por bin
    porcentaje_morosidad = {
        rango: round((intereses[rango] / total) * 100, 2)
        for rango, total in totales_dict.items()
        if rango in intereses
    }
    
    # Generamos un df para graficar
    df_plot = pd.DataFrame({'Rango': list(porcentaje_morosidad.keys()), 'Porcentaje de Morosos': list(porcentaje_morosidad.values())})
    orden_rangos = ['<11%', '11% - 16%', '16% - 21%', '21% - 26%', '>26%']
    df_plot['Rango'] = pd.Categorical(df_plot['Rango'], categories=orden_rangos, ordered=True)
    df_plot = df_plot.sort_values('Rango')

    # Graficamos
    fig = px.bar(
        df_plot,
        x='Rango',
        y='Porcentaje de Morosos',
        text='Porcentaje de Morosos',
        labels={'Rango': 'Rango de Tasa de Interés', 'Porcentaje de Morosos': 'Morosidad (%)'},
        # title=dict(text='Porcentaje de Morosos por<br>Rango de Tasa de Interés', x=0.5),
        width=320,
    )

    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(yaxis_tickformat='.2f', yaxis_range=[0, max(df_plot['Porcentaje de Morosos']) + 1],
                      title=dict(text='Porcentaje de Morosos por<br>Rango de Tasa de Interés', x=0.5),
                      margin=dict(l=20, r=0, t=100, b=10), plot_bgcolor='white',)

    return fig
