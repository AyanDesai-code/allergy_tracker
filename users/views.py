from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from urllib3 import request
from .models import CustomUser
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote_plus, urlencode
import json
from authlib.integrations.django_client import OAuth
from django.views.decorators.csrf import csrf_exempt


from .models import Menu, Restaurant, Menu_Section

# Create your views here.
def users(request):
    myusers = CustomUser.objects.all().values()
    template = loader.get_template('all_users.html')
    context = {
        'myusers': myusers,
    }
    return HttpResponse(template.render(context,request))

def details(request, id):
    myuser = CustomUser.objects.get(id=id)
    template = loader.get_template('user_details.html')
    context = {
        'myuser':myuser
    }
    return HttpResponse(template.render(context,request))


oauth = OAuth()

oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)

def login(request):
    return oauth.auth0.authorize_redirect(
        request, request.build_absolute_uri(reverse("callback"))
    )

def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    request.session["user"] = token
    return redirect(request.build_absolute_uri(reverse("index")))

def logout(request):
    request.session.clear()

    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("index")),
                "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )


def index(request):
    return render(
        request,
        "index.html",
        context={
            "session": request.session.get("user"),
            "pretty": json.dumps(request.session.get("user"), indent=4),
        },
    )

@csrf_exempt
def menus(request, user_id):
   user = get_object_or_404(CustomUser, id=user_id)

   restaurants = Restaurant.objects.filter(owner=user)
   menus = Menu.objects.filter(restaurant__in=restaurants).distinct()



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
            name = data.get('name')
            restaurant_id = data.get('restaurant')
            section_ids = data.get('sections', [])

            restaurant = Restaurant.objects.get(id=restaurant_id)
            new_menu = Menu.objects.create(name=name)
            new_menu.sections.set(Menu_Section.objects.filter(id__in=section_ids))
            new_menu.restaurant = restaurant
            new_menu.save()


            return JsonResponse({'status': 'created', 'menu_id': new_menu.id}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


   if request.GET.get('search'):
        menus = menus.filter(name__icontains=request.GET.get('search'))

   context = {
        'menus': menus,
        'myuser': user
    }
   
   return render(request, 'user_details.html', context)

def delete_menu(request, id):
   menu = get_object_or_404(Menu, id=id)

   restaurant = menu.restaurant
   if restaurant:
        menu.restaurant = None
        menu.save()


   return redirect('details', id=restaurant.owner.id if restaurant else None)


def update_menu(request, id):
    menu = get_object_or_404(Menu, id=id)
    restaurant = menu.restaurant


    
    user = restaurant.owner if restaurant else None

    if request.method == 'POST':
        name = request.POST.get('name')
        restaurant_id = request.POST.get('restaurant')
        section_ids = request.POST.getlist('sections')

        menu.name = name
        menu.sections.set(Menu_Section.objects.filter(id__in=section_ids))
        # Move menu to new restaurant
        
        new_restaurant = Restaurant.objects.get(id=restaurant_id)
        menu.restaurant = new_restaurant
        menu.save()


        return redirect('user_details', user_id=user.id)

    
    return render(request, 'user_details.html', {'myuser': user, 'menus': menus, 'selected_menu': menu})


def menu_details(request, id):
    menu = get_object_or_404(Menu, id=id)
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': menu.id,
            'name': menu.name,
            'restaurant': menu.restaurant.id if menu.restaurant else None,
            'sections': list(menu.sections.values_list('id', flat=True)),
        })
    return render(request, 'user_details.html', {'mymenu': menu})

def main(request):
  return render(request, 'user_details.html', {'myuser': request.user})

@csrf_exempt
def menu_sections(request, user_id):
   user = get_object_or_404(CustomUser, id=user_id)
   restaurants = Restaurant.objects.filter(owner=user)
   menus = Menu.objects.filter(restaurant__in=restaurants).distinct()
   menu_sections = Menu_Section.objects.all() 


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
            title = data.get('title')
            menu_id = data.get('menu_id')

            if not title or not menu_id:
                return JsonResponse({'error': 'title and menu_id are needed buckaroo'}, status=400)

            menu = Menu.objects.get(id=menu_id)
            new_section = Menu_Section.objects.create(title=title)

            menu.sections.add(new_section)




            return JsonResponse({'status': 'created', 'menu_section_id':new_section.id}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


   if request.GET.get('search'):
       menu_sections = menu_sections.filter(title__icontains=request.GET.get('search'))

   context = {
        'menus': menus,
        'myuser': user,
        'menu_sections': menu_sections
    }
   
   return render(request, 'user_details.html', context)

def delete_menu_section(request, id):
   menu_section = get_object_or_404(Menu_Section, id=id)
   menus = Menu.objects.filter(sections=menu_section)
   
   owner = None
   if menus.exists():
       owner = menus.first().restaurant.owner

   for menu in menus:
       menu.sections.remove(menu_section)
   menu_section.delete()
 
   if owner:
         return redirect('user_details', user_id=owner.id)
   return redirect('users')
    

def update_menu_section(request, id):
    menu_section = get_object_or_404(Menu_Section, id=id)
    menu = menu_section.menu_set.first()
    restaurant = menu.restaurant if menu else None
    user = restaurant.owner if restaurant else None

    if request.method == 'POST':
        title = request.POST.get('title')
        menu_id = request.POST.get('menu_id')
        
        if title: 
            menu_section.title = title

        if menu_id:
            new_menu = get_object_or_404(Menu, id=menu_id)
            menu_section.menu_set.clear()
            menu_section.menu_set.add(new_menu)

        menu_section.save()
        return redirect('user_details', user_id=user.id if user else None)

    menus = restaurant.menus.all() if restaurant else Menu.objects.none()
    return render(request, 'user_details.html',{
        'myuser': user,
        'menus': menus,
        'selected_menu': menu,
        'selected_menu_section': menu_section
    })
    


def menu_section_details(request, id):
    menu_section = get_object_or_404(Menu_Section, id=id)
    menus = menu_section.menu_set_all()
    restaurant = menus.first().restaurant if menus.exists() else None

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': menu_section.id,
            'title': menu_section.title,
            'restaurant': menu_section.restaurant.id if menu_section.restaurant else None,
            'sections': list(menu_section.sections.values_list('id', flat=True)),
        })
    return render(request, 'user_details.html', {'menu_section': menu_section})

def main(request):
  return render(request, 'user_details.html', {'myuser': request.user})
