from django.shortcuts import render
# from django.views import generic
# from django.shortcuts import get_object_or_404
# from django.http import HttpResponse
from .models import Coffee, Tea, Syrup

# Create your views here.

def index(request):
    coffees = Coffee.objects.all().order_by('-is_available')
    teas = Tea.objects.all().order_by('-is_available')
    syrups = Syrup.objects.all().order_by('-is_available')
    
    context = {
        'coffees': coffees,
        'teas': teas,
        'syrups': syrups,
        # 'all_products': list(coffees) + list(teas) + list(syrups),
    }
    
    return render(request, 'products/index.html', context)

def coffee_list(request):
    coffees = Coffee.objects.all().order_by('-is_available')
    return render(request, 'products/coffee_list.html', {"coffees": coffees})

def tea_list(request):
    teas = Tea.objects.all().order_by('-is_available')
    return render(request, 'products/tea_list.html', {"teas": teas})

def syrup_list(request):
    syrups = Syrup.objects.all().order_by('-is_available')
    return render(request, 'products/syrup_list.html', {"syrups": syrups})

def delivery_info(request):
    return render(request, 'products/delivery_info.html')

# def coffee_detail(request, pk):
#     coffee = get_object_or_404(Coffee, pk=pk)
#     return render(request, 'products/coffee_detail.html', {'coffee': coffee})

# def tea_detail(request, pk):
#     tea = get_object_or_404(Tea, pk=pk)
#     return render(request, 'products/tea_detail.html', {'tea': tea})

# def syrup_detail(request, pk):
#     syrup = get_object_or_404(Syrup, pk=pk)
#     return render(request, 'products/syrup_detail.html', {'syrup': syrup})

# def search(request):
#     query = request.GET.get('q', '')
#     products = Product.objects.filter(name__icontains=query) # Поиск по части названия
#     return render(request, 'search_results.html', {'products': products, 'query': query})