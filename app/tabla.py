import pandas as pd
import plotly.graph_objects as go

def generar_tabla_resumen_prestamos(filtross, collection):
    """
    Recibe un diccionario con los filtros:
    {
        'estado': [...],
        'tipo_propiedad': [...],
        'duracion': [...]
    }
    Devuelve una tabla resumen como figura Plotly
    """

    # Copia de los filtros para evitar modificar el original
    filtros = filtross.copy()
    if filtros['tipo_propiedad'] == ['Hipoteca', 'Alquilada', 'Propia']:
        filtros['tipo_propiedad'] = ['Hipoteca', 'Alquilada', 'Propia', 'ANY']
    # reemplazar Alquilada por Renta si es que existe
    if 'Alquilada' in filtros['tipo_propiedad']:
        filtros['tipo_propiedad'] = ['Renta' if x == 'Alquilada' else x for x in filtros['tipo_propiedad']]

    # Construir consulta
    query = {}
    if filtros.get('region'):
        query['estado'] = {'$in': filtros['region']}
    if filtros.get('tipo_propiedad'):
        query['tipo_vivienda'] = {'$in': filtros['tipo_propiedad']}
    if filtros.get('duracion'):
        query['termino_prestamo'] = {'$in': filtros['duracion']}

    # Obtener datos
    datos = list(collection.find(query, {'_id': 0}))
    if not datos:
        return go.Figure()

    df = pd.DataFrame(datos)

    # Calcular agregados
    total_prestamos = int(df["num_prestamos"].sum())
    monto_promedio = round(df["monto_promedio"].mean(), 2)
    interes_promedio = round(df["interes_promedio"].mean(), 2)
    tasa_morosidad = f"{round(df['tasa_morosidad'].mean(), 2)}%"

    # Crear tabla Plotly
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=["<b>Métrica</b>", "<b>Valor</b>"],
                fill_color='lightblue',
                align='left',
                font=dict(size=14)
            ),
            cells=dict(
                values=[
                    ["# de Préstamos", "Monto promedio", "Interés promedio", "Tasa de Morosidad"],
                    [total_prestamos, monto_promedio, interes_promedio, tasa_morosidad]
                ],
                fill_color='white',
                align='left',
                font=dict(size=13)
            )
        )
    ])

    fig.update_layout(
        title=dict(text='Resumen Global de Préstamos', x=0.5),
        height=300,
        margin=dict(l=30, r=30, t=50, b=30)
    )

    return fig
