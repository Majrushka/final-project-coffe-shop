from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Coffee, Tea, Syrup
from django.core.paginator import Paginator

# Create your views here.

def index(request):
    coffees = Coffee.objects.all().order_by('-is_available')
    teas = Tea.objects.all().order_by('-is_available')
    syrups = Syrup.objects.all().order_by('-is_available')
    
    context = {
        'coffees': coffees,
        'teas': teas,
        'syrups': syrups,
    }
    
    return render(request, 'products/index.html', context)

def coffee_list(request):
    coffees = Coffee.objects.all().order_by('-is_available')
    paginator = Paginator(coffees, 4)
    page_number = request.GET.get('page', 1)
    coffees = paginator.get_page(page_number)
    return render(request, 'products/coffee_list.html', {"coffees": coffees})

def tea_list(request):
    teas = Tea.objects.all().order_by('-is_available')
    return render(request, 'products/tea_list.html', {"teas": teas})

def syrup_list(request):
    syrups = Syrup.objects.all().order_by('-is_available')
    return render(request, 'products/syrup_list.html', {"syrups": syrups})

def delivery_info(request):
    return render(request, 'products/delivery_info.html')

def coffee_detail(request, pk):
    coffee = get_object_or_404(Coffee, pk=pk)
    return render(request, 'products/coffee_detail.html', {'coffee': coffee})

def tea_detail(request, pk):
    tea = get_object_or_404(Tea, pk=pk)
    return render(request, 'products/tea_detail.html', {'tea': tea})

def syrup_detail(request, pk):
    syrup = get_object_or_404(Syrup, pk=pk)
    return render(request, 'products/syrup_detail.html', {'syrup': syrup})

def product_search(request):
    query = request.GET.get('q', '').strip().title()
    results = []
    
    if query in ['кофе', 'coffee']:
        return redirect('coffee_list')
    elif query in ['чай', 'чаи', 'tea']:
        return redirect('tea_list')
    elif query in ['сироп', 'сиропы', 'syrup']:
        return redirect('syrup_list')
    
    results = []

    if query:
        coffee_results = Coffee.objects.filter(name__iexact=query)
        tea_results = Tea.objects.filter(name__iexact=query)
        syrup_results = Syrup.objects.filter(name__iexact=query)
        
        results = list(coffee_results) + list(tea_results) + list(syrup_results)
        
        if not results:
            coffee_results = Coffee.objects.filter(name__icontains=query)
            tea_results = Tea.objects.filter(name__icontains=query)
            syrup_results = Syrup.objects.filter(name__icontains=query)
            results = list(coffee_results) + list(tea_results) + list(syrup_results)
        
        if len(results) == 1:
            product = results[0]
            if isinstance(product, Coffee):
                return redirect('coffee_detail', pk=product.pk)
            elif isinstance(product, Tea):
                return redirect('tea_detail', pk=product.pk)
            elif isinstance(product, Syrup):
                return redirect('syrup_detail', pk=product.pk)
    
    return render(request, 'products/search_results.html', {
        'results': results,
        'query': query,
    })