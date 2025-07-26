from django.shortcuts import render
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
   return HttpResponse(template.render(context, request))

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