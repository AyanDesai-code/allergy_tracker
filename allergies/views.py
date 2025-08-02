from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import get_user_model
from .models import Allergy
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



CustomUser= get_user_model()

# Create your views here.
@csrf_exempt
def allergies(request, user_id):
   user = get_object_or_404(CustomUser, id=user_id)
   queryset = user.allergies.all()

   # if request.method == 'POST':
   #    data = request.POST
   #    allergyname = data.get('allergyname')
   #    test_level = data.get('test_level')
   #    category = data.get('category')

   #    new_allergy = Allergy.objects.create(
   #    allergyname=allergyname,
   #    test_level=test_level,
   #    category=category,
   #  )
   #    user.allergies.add(new_allergy)

   #    return redirect('user_details', user_id=user.id)
   if request.method == 'POST':
      try:
         data = json.loads(request.body)
         allergyname = data.get('allergyname')
         test_level = data.get('test_level')
         category = data.get('category')

         new_allergy = Allergy.objects.create(
            allergyname=allergyname,
            test_level=test_level,
            category=category,
            )
         user.allergies.add(new_allergy)

         return JsonResponse({'status': 'created', 'allergy_id': new_allergy.id}, status=201)

      except json.JSONDecodeError:
         return JsonResponse({'error': 'Invalid JSON'}, status=400)



   if request.GET.get('search'):
      queryset = queryset.filter(allergyname__icontains=request.GET.get('search'))
   
   context = {
      'myallergies':queryset, 'myuser':user
   }   
   return render(request, 'user_details.html', context)

def delete_allergy(request, id):
   allergy = get_object_or_404(Allergy, id=id)
   user = allergy.customuser_set.first()
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
    allergy = get_object_or_404(Allergy, id=id)
    
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': allergy.id,
            'allergyname': allergy.allergyname,
            'test_level': allergy.test_level,
            'category': allergy.category,
        })
    
    return render(request, 'details.html', {'myallergy': allergy})
def main(request):
  template = loader.get_template('user_details.html')
  return HttpResponse(template.render())
