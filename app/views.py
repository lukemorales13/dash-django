from django.shortcuts import render
import plotly.io as pio
from pymongo import MongoClient
from .grafico_fico_vs_intereses import generar_grafico_fico_vs_interes
from .morosos_vs_intereses import grafico_morosos_intereses
from .ingreso_por_grado_filtrado import generar_grafico_ingreso_por_grado
from .tabla import generar_tabla_resumen_prestamos
from .grafica1_corregida import obtener_figura_1
from .highlights import highlights
from .grafica_intereses import crear_grafica_intereses
import concurrent.futures

cliente = MongoClient('mongodb://localhost:27017/')
bd = cliente['lendingclub']
REGIONES = [
  'Alabama',              'Alaska',              'Arizona',
  'Arkansas',             'California',          'Carolina del Norte',
  'Carolina del Sur',     'Colorado',            'Connecticut',
  'Dakota del Norte',     'Dakota del Sur',      'Delaware',
  'Distrito de Columbia', 'Florida',             'Georgia',
  'Hawái',                'Idaho',               'Illinois',
  'Indiana',              'Kansas',              'Kentucky',
  'Luisiana',             'Maine',               'Maryland',
  'Massachusetts',        'Minnesota',           'Misisipi',
  'Misuri',               'Montana',             'Míchigan',
  'Nebraska',             'Nevada',              'Nueva Jersey',
  'Nueva York',           'Nuevo Hampshire',     'Nuevo México',
  'Ohio',                 'Oklahoma',            'Oregón',
  'Pensilvania',          'Rhode Island',        'Tennessee',
  'Texas',                'Utah',                'Vermont',
  'Virginia',             'Virginia Occidental', 'Washington',
  'Wisconsin',            'Wyoming',             'Todas'
]
TIPO_PROP_VIVIENDAS = ['Hipoteca', 'Alquilada', 'Propia', 'Todas']
DURACION = ['36 meses', '60 meses', 'Todas']


def main_dashboard(request):
    # Manejo de propiedades
    
    prop_values = request.GET.get('tipo_propiedad', '')
    selected_propiedades = [x for x in prop_values.split(',') if x]
    
    # Si está vacío o contiene "Todas", usar todas las opciones (excepto "Todas")
    if not selected_propiedades or 'Todas' in selected_propiedades:
        selected_propiedades = [x for x in TIPO_PROP_VIVIENDAS if x != 'Todas']
    
    # Manejo de regiones (misma lógica)
    region_values = request.GET.getlist('region')
    # selected_regiones = region_values
    if len(region_values) == 1 and ',' in region_values[0]:
        selected_regiones = [x for x in region_values[0].split(',') if x]
    else:
        selected_regiones = region_values

    if not selected_regiones or 'Todas' in selected_regiones:
        selected_regiones = [x for x in REGIONES if x != 'Todas']

    duracion_values = request.GET.get('duracion', '')
    selected_duracion = [x for x in duracion_values.split(',') if x]
    
    # Si está vacío o contiene "Ambos", usar ambas opciones (excepto "Ambos")
    if not selected_duracion or 'Todas' in selected_duracion:
        selected_duracion = [x for x in DURACION if x != 'Todas']

    filtros = {
        'region': selected_regiones,
        'tipo_propiedad': selected_propiedades,
        'duracion': selected_duracion
    }

    tasks = [
        (generar_grafico_fico_vs_interes, (filtros, bd['prestamos_analitica'])),
        (highlights, (filtros, bd['ultimosMesesPrestamos'], bd['morososPrestamos'], bd['ultimosMesesGanancias'])),
        (crear_grafica_intereses, (filtros, bd['loanColeccion'])),
        (generar_grafico_ingreso_por_grado, (filtros, bd['ingresos_por_grado'])),
        (grafico_morosos_intereses, (filtros, bd["morosidadInteres"])),
        (generar_tabla_resumen_prestamos, (filtros, bd['analisis_prestamos'])),
        (obtener_figura_1, (filtros, bd['loanColeccion'])),
    ]

    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_task = {
            executor.submit(func, *args): idx for idx, (func, args) in enumerate(tasks)
        }
        results = [None] * len(tasks)
        for future in concurrent.futures.as_completed(future_to_task):
            idx = future_to_task[future]
            results[idx] = future.result()

    fig_fico, fig_highlights, fig_ganXgrado, fig_ingXgrado, fig_morosos, fig_tabla, fig_linea = results

    return render(request, 'content.html', {
        'fig_fico' : pio.to_html(fig_fico, include_plotlyjs='cdn'),
        'highlight_plot': pio.to_html(fig_highlights, include_plotlyjs='cdn'),
        'fig_ganXgrado': pio.to_html(fig_ganXgrado, include_plotlyjs='cdn'),
        'fig_ingXgrado': pio.to_html(fig_ingXgrado, include_plotlyjs='cdn'),
        'fig_morosos': pio.to_html(fig_morosos, include_plotlyjs='cdn'),
        'fig_tabla': pio.to_html(fig_tabla, include_plotlyjs='cdn'),
        'fig_linea': pio.to_html(fig_linea, include_plotlyjs='cdn'),
        'selected_propiedades': selected_propiedades,
        'selected_regiones': selected_regiones,
        'selected_duracion': selected_duracion, 
        'all_propiedades': TIPO_PROP_VIVIENDAS,
        'all_regiones': REGIONES,
        'all_duracion': DURACION
    })