from django.shortcuts import render

# Create your views here.

def main_dashboard(request):
    context = {}
    return render(request, 'content.html', context)