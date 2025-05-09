from django.shortcuts import render
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
import random 

# Create your views here.

VARIABLES = ['A', 'B', 'C', 'D']
def main_dashboard(request):
    regions = request.GET.getlist('region')
    
    if not regions:
        regions = VARIABLES

    y = [random.randint(5, 20) for _ in regions]
    fig = go.Figure(data=go.Bar(x=regions, y=y, name="Ventas"))
    chart_html = pio.to_html(fig, include_plotlyjs='cdn')

    return render(request, 'content.html', {
        'plot': chart_html,
        'regions': regions,
        'all': VARIABLES,
    })