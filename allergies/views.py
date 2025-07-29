from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import get_user_model
from .models import Allergy

CustomUser= get_user_model()

# Create your views here.
def allergies(request, user_id):
   user = get_object_or_404(CustomUser, id=user_id)
   queryset = user.allergies.all()

   if request.method == 'POST':
      data = request.POST
      allergyname = data.get('allergyname')
      test_level = data.get('test_level')
      category = data.get('category')

      new_allergy = Allergy.objects.create(
      allergyname=allergyname,
      test_level=test_level,
      category=category,
    )
      user.allergies.add(new_allergy)

      return redirect('user_details', user_id=user.id)


   if request.GET.get('search'):
      queryset = queryset.filter(allergyname__icontains=request.GET.get('search'))
   
   context = {
      'myallergies':queryset, 'myuser':user
   }   
   return render(request, 'user_details.html', context)

def delete_allergy(request, id):
   allergy = get_object_or_404(Allergy, id=id)
   
   user.allergies.remove(allergy)
   return redirect('user_details', user_id=user.id)

def update_allergy(request, id):
   allergy = get_object_or_404(Allergy, id=id)

   user = allergy.customuser_set.first() 

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
      return redirect('user_details', user_id=user.id)
   
   allergies = user.allergies.all()
   return render(request, 'user_details.html', {'myuser': user, 'allergies': allergies, 'selected_allergy': allergy})


def details(request, id):
   user = get_object_or_404(CustomUser, id=id)
   allergies = user.allergies.all()
   return render(request, 'user_details.html', {'myuser': user, 'allergies': allergies})


