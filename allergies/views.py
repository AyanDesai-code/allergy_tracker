from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import Allergy

# Create your views here.
def allergies(request):
   myallergies = Allergy.objects.all().values()
   template = loader.get_template('all_allergies.html')
   context = {
      'myallergies':myallergies,
   }
   if request.method == 'POST':
      data = request.POST
      allergyname = data.get('allergyname')
      test_level = data.get('test_level')
      category = data.get('category')

      Allergy.objects.create(
         allergyname=allergyname,
         test_level = test_level,
         category = category,

      )
      return redirect('/')
   queryset = Allergy.objects.all()
   if request.GET.get('search'):
      queryset = queryset.filter(allergyname__icontains=request.GET.get('search'))
   
   context = {'allergies' : queryset}
   return HttpResponse(template.render(context, request))

def delete_allergy(request, id):
   allergy = get_object_or_404(Allergy, id=id)
   allergy.delete()
   return redirect ('/')

def update_allergy(request, id):
   if request.method == 'POST':
      data = request.POST
      allergyname = data.get('allergyname')
      test_level = data.get('test_level')
      category = data.get('category')

      allergy.allergyname = allergyname
      allergy.test_level = test_level
      allergy.category = category
      allergy.save()
      context = {'allergy': allergy}
      return render (request 'details.html', context)
def details(request, id):
   myallergy = Allergy.objects.get(id=id)
   template = loader.get_template('details.html')
   context = {
      'myallergy': myallergy
   }
   return HttpResponse(template.render(context,request))
def main(request):
   template = loader.get_template('main.html')
   return HttpResponse(template.render())