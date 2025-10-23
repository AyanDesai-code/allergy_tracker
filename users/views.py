#I dont need half of these imports, but im too scared to delete them :(
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from urllib3 import request
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote_plus, urlencode
import json
from authlib.integrations.django_client import OAuth
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from authlib.integrations.django_client import OAuth
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
import requests

from allergies.models import Allergy
from .models import CustomUser, Restaurant, Menu, Menu_Section, Food, Food_Allergen

# Create your views here.

#---------------
#Users
#---------------
oauth = OAuth()
#registers things with auth0
auth0 = oauth.register(
    'auth0',
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={'scope': 'openid profile email'},
    server_metadata_url=f'https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration'
)
#views for users and auth0 things with users
def users(request):
    myusers = CustomUser.objects.all().values()
    template = loader.get_template('all_users.html')
    context = {
        'myusers': myusers,
        "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
        "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
        "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
    }
    return HttpResponse(template.render(context,request))
#thing to redirect users to details
def details(request, id):
    myuser = CustomUser.objects.get(id=id)
    template = loader.get_template('user_details.html')
    context = {
        'myuser':myuser,
        "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
        "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
        "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
    }
    return HttpResponse(template.render(context,request))


#view to login (DONT TOUCH)
def login(request):
    print("Hola!")
    return auth0.authorize_redirect(request, settings.AUTH0_CALLBACK_URL)
#callback return back to site after auth0 login (DONT TOUCH)
@csrf_exempt
def callback(request):
    print("Hello!")
    code = request.GET.get("code")
    token_url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"

    # Exchange code for tokens
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "client_secret": settings.AUTH0_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
    }

    # ✅ Use requests.post instead of request.post
    token_res = requests.post(token_url, json=token_data).json()

    user_url = f"https://{settings.AUTH0_DOMAIN}/userinfo"
    # ✅ Use requests.get instead of request.get
    user_info = requests.get(
        user_url,
        headers={"Authorization": f"Bearer {token_res['access_token']}"}
    ).json()

    # Use email to check DB
    email = user_info.get("email")
    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            "username": user_info.get("name", email.split("@")[0]),
        }
    )

    # Attach to Django session
    request.session["user"] = user_info

    return redirect("/")

#logout for auth0
def logout(request):
    request.session.clear()

    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": settings.AUTH0_HOME_URL,
                # "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )

#index view for users
def index(request):
    user_session = request.session.get('user')

    if user_session:
        email = user_session.get('email')
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "username": user_session.get("name", email.split("@")[0]),
                'is_authenticated': True
                # add other defaults if needed
            },
        )
    else:
        # fallback to authenticated user if using Django auth
        user = request.user if request.user.is_authenticated else None

    user = "None"

    if user:
        restaurants = Restaurant.objects.filter(owner=user)
        menus = Menu.objects.filter(restaurant__in=restaurants).distinct()
    else:
        restaurants = Menu.objects.none()
        menus = Menu.objects.none()

    # menu_sections = Menu_Section.objects.filter(menu__in=menus)
    foods = Food.objects.filter(menu_section__in=menu_sections)
    food_allergens = Food_Allergen.objects.filter(food__in=foods)

    context = {
        "myuser": user,
        "restaurants": restaurants,
        "menus": menus,
        # "menu_sections": menu_sections,
        "foods": foods,
        "food_allergens": food_allergens,
        "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
        "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
        "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
        "allergies": Allergy.objects.all(),
    }

    return render(request, "user_details.html", context)

#tests to see if sessions are working useful for the 'mismatching state error' :(
def test_session(request):
    request.session['foo'] = 'bar'
    return HttpResponse(f"Session foo={request.session.get('foo')}")



#---------------
#Menus
#---------------
#Creates menus
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

            restaurant = get_object_or_404(Restaurant, id=restaurant_id)
            new_menu = Menu.objects.create(name=name, restaurant=restaurant)
            new_menu.sections.set(Menu_Section.objects.filter(id__in=section_ids))
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
        'myuser': user,
        "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
        "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
        "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
    }
   
   return render(request, 'user_details.html', context)
#deletes menus and removes relationships (not used), but could be useful later
def delete_menu(request, id):
   menu = get_object_or_404(Menu, id=id)

   restaurant = menu.restaurant
   if restaurant:
        menu.restaurant = None
        menu.save()


   return redirect('details', id=restaurant.owner.id if restaurant else None)

#updates menus (not used), but could be useful later
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

    
    return render(request, 'user_details.html', {'myuser2': user, 'menus': menus, 'selected_menu': menu})

#the details for the menu in json or html
def menu_details(request, id):
    menu = get_object_or_404(Menu, id=id)
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': menu.id,
            'name': menu.name,
            'restaurant': menu.restaurant.id if menu.restaurant else None,
            'sections': list(menu.sections.values_list('id', flat=True)),
            "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
            "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
            "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
        })
    return render(request, 'user_details.html', {'mymenu': menu})

#creates menu sections 
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
            menu_section_id = data.get('menu_section_id')

            if not title or not menu_section_id:
                return JsonResponse({'error': 'title and menu_section_id are needed buckaroo'}, status=400)

            menu = Menu.objects.get(id=menu_section_id)
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
        'menu_sections': menu_sections,
        "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
        "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
        "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
    }
   
   return render(request, 'user_details.html', context)
#provides a way to delete menu sections and removes relationships (not used), but could be useful later
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
    
# provides a way to update menu sections (not used), but could be useful later
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
    

#the details for the menu sections in json or html
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
            "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
            "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
            "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
        })
    return render(request, 'user_details.html', {'menu_section': menu_section})
@csrf_exempt
#creates food allergens
def food_allergens(request, food_allergen_id):
   food_allergen = get_object_or_404(Food_Allergen, id=food_allergen_id)


   if request.method == 'POST':
        allergen_name = request.POST.get('allergen')
        if not allergen_name:
            return JsonResponse({'error': 'Allergen name is required'}, status=400)
        
        try:
            new_allergy = Allergy.objects.create(allergen=allergen_name)
            food_allergen.allergies.add(new_allergy)
            print(f"Added Allergy {new_allergy.allergen} to Food_Allergen {food_allergen.allergen}")

            return JsonResponse({'status': 'created', 'food_allergen_id': new_allergy.id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
   food_allergens = Food_Allergen.objects.all()
   search_query = request.GET.get('search')
   if search_query:
       food_allergens = food_allergens.filter(allergen__icontains=search_query)

   context = {
        'food_allergens': food_allergens,
        "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
        "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
        "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
    }
   
   return render(request, 'user_details.html', context)
#deletes food allergens and removes relationships  (not used), but could be useful later
def delete_food_allergen(request, id):
   food_allergen = get_object_or_404(Food_Allergen, id=food_allergen_id)

    # Remove relationships before deleting
   menu_sections = food_allergen.menu_sections.all()
   for section in menu_sections:
        section.food_allergens.remove(food_allergen)

   food_allergen.delete()

    # Redirect back to the referring page or a safe fallback
   return redirect(request.META.get('HTTP_REFERER', 'food_allergens'))

#provides a way to update food allergens (not used), but could be useful later
def update_food_allergen(request, id):
    food_allergen = get_object_or_404(Food_Allergen, id=id)

    if request.method == 'POST':
        new_allergen = request.POST.get('allergen')

        # Accept any non-empty free-text allergen value now that `Food_Allergen`
        # stores plain text instead of choice keys.
        if not new_allergen:
            return HttpResponse("Allergen value is required.", status=400)

        food_allergen.allergen = new_allergen
        food_allergen.save()
        return redirect("food_allergens")
        
    return redirect('user_details', {"food_allergen": food_allergen})

    

#the details for the food allergens in json or html
def food_allergen_details(request, id):
    food_allergen = get_object_or_404(Food_Allergen, id=id)

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'allergen': food_allergen.allergen,
            'id': food_allergen.id,
            "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
            "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
            "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
        })
    return render(request, 'user_details.html', {'food_allergen': food_allergen})
#creates foods
@csrf_exempt
def Foods(request, user_id):
   user = get_object_or_404(CustomUser, id=user_id)
   restaurants = Restaurant.objects.filter(owner=user)
   menus = Menu.objects.filter(restaurant__in=restaurants).distinct()
   menu_sections = Menu_Section.objects.all() 
   food_allergens = Food_Allergen.objects.all()
   foods = Food.objects.all()


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
            allergen_ids = data.get('allergies', [])
            section_id = data.get('section')

            if not name or not section_id:
                return JsonResponse({'error': 'name and section are needed buckaroo'}, status=400)
            
            section = get_object_or_404(Menu_Section, id=section_id)
            new_food = Food.objects.create(name=name, section=section)
            new_food.allergies.set(Allergy.objects.filter(id__in=allergen_ids))
            new_food.save()
            #-tells error so I dont go insane debugging this code
            return JsonResponse({'status': 'created', 'food_id': new_food.id}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

   search_query = request.GET.get('search')
   if search_query:
       foods = foods.filter(name__icontains=search_query)

#provides context for foods
   context = {
        'menus': menus,
        'myuser': user,
        'menu_sections': menu_sections,
        'food_allergens': food_allergens,
        'foods': foods,
        "AUTH0_DOMAIN": settings.AUTH0_DOMAIN, 
        "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
        "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,

    }
   
   return render(request, 'user_details.html', context)
#provides a way to delete foods (not used), but could be useful later
def delete_foods(request, id):
  food = get_object_or_404(Food, id=id)
  food.delete()
  return redirect(request.META.get('HTTP_REFERER', 'foods'))
    
# provides a way to update foods (not used), but could be useful later
def update_foods(request, id):
    food = get_object_or_404(Food, id=id)
    section = food.section
    restaurant = section.menu_set.first().restaurant if section.menu_set.exists() else None
    user = restaurant.owner if restaurant else None
    
    if request.method == 'POST':
        name = request.POST.get('name')
        section_id = request.POST.get('section')
        allergen_ids = request.POST.getlist('allergies')
        if name:
            food.name = name

        if section_id:
            new_section = get_object_or_404(Menu_Section, id=section_id)
            food.section = new_section

        if allergen_ids:
            food.allergies.set(Allergy.objects.filter(id__in=allergen_ids))

        food.save()
        return redirect('user_details', user_id=user.id if user else None)

    menu_sections = restaurant.menu_sections.all() if restaurant else Menu_Section.objects.none()
    food_allergens = Food_Allergen.objects.all()
    return render(request, 'user_details.html', {
        'myuser': user,
        'menu_sections': menu_sections,
        'food_allergens': food_allergens,
        'selected_food': food
    })
    

#the details for the foods in json or html
def foods_details(request, id):
    food = get_object_or_404(Food, id=id)
    section = food.section
    restaurant = section.menu_set.first().restaurant if section.menu_set.exists() else None

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': food.id,
            'name': food.name,
            'section': food.section.id if food.section else None,
            'allergies': list(food.allergies.values_list('id', flat=True)),
            "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
            "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
            "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
        })
    return render(request, 'user_details.html', {'food': food})

@csrf_exempt
def Restaurants(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Basic restaurant fields
            name = data.get('name')
            location = data.get('location')
            description = data.get('description', '')
            phone_number = data.get('phone_number', '')

            if not name or not location:
                return JsonResponse({'error': 'name and location are needed buckaroo'}, status=400)

            # Create restaurant
            #creates the restaurant
            new_restaurant = Restaurant.objects.create(
                owner=user,
                name=name,
                location=location,
                description=description,
                phone_number=phone_number
            )
            print(f"[DEBUG] Created Restaurant: id={new_restaurant.id}, name={new_restaurant.name}, location={new_restaurant.location}")

            # Handle menus, sections, and foods
            # debug statements to make sure the creation is happening correctly
            menus_data = data.get('menus', [])
            for menu_data in menus_data:
                menu_name = menu_data.get('name')
                menu_obj = Menu.objects.create(name=menu_name, restaurant=new_restaurant)
                print(f"[DEBUG] Created Menu: id={menu_obj.id}, name={menu_obj.name}, restaurant_id={new_restaurant.id}")

                for section_data in menu_data.get('sections', []):
                    section_title = section_data.get('title')
                    section_obj = Menu_Section.objects.create(title=section_title)
                    menu_obj.sections.add(section_obj)

                    for food_data in section_data.get('foods', []):
                        food_name = food_data.get('name')
                        allergens_list = food_data.get('allergens', [])

                        food_obj = Food.objects.create(name=food_name, section=section_obj)
                        print(f"[DEBUG] Created Food: id={food_obj.id}, name={food_obj.name}, section_id={section_obj.id}")

                        for allergen_name in allergens_list:
                            allergen_obj = Food_Allergen.objects.filter(allergen__iexact=allergen_name).first()
                            if allergen_obj:
                                food_obj.allergies.add(allergen_obj)
                                print(f"[DEBUG] Added Food_Allergen '{allergen_obj.allergen}' (id={allergen_obj.id}) to Food id={food_obj.id}")
                            else:
                                print(f"[DEBUG] Food_Allergen '{allergen_name}' not found in Food_Allergen table for Food id={food_obj.id}")
                        # Print all Food_Allergen objects for this food after assignment
                        print(f"[DEBUG] Food id={food_obj.id} Food_Allergens after assignment: {[a.allergen for a in food_obj.allergies.all()]}")

            return JsonResponse({'status': 'created', 'restaurant_id': new_restaurant.id}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    # Optionally handle GET requests here
    return JsonResponse({'message': 'Only POST supported'}, status=405)


#this provides a way to delete restaurants (not used), but could be useful later
def delete_restaurants(request, id):
  restaurant = get_object_or_404(Restaurant, id=id)
  owner = restaurant.owner  
  # Remove the restaurant from all menus
  for menu in menus:
      menu.restaurant = None
      menu.save()
  
  # Delete the restaurant
  restaurant.delete()

  return redirect('user_details', user_id=owner.id if owner else None)

#this provides a way to update the restaurant (not used), but could be useful later
def update_restaurant(request, id):
    restaurant = get_object_or_404(Restaurant, id=id)
    user = restaurant.owner

    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        description = request.POST.get('description')
        phone_number = request.POST.get('phone_number')
        section_id = request.POST.get('section')
        allergen_ids = request.POST.getlist('allergies')

        if name:
            restaurant.name = name
    
        if location:
            restaurant.location = location 
        if description:
            restaurant.description = description

        if phone_number:
            restaurant.phone_number = phone_number

        restaurant.save()

        return redirect('user_details', user_id=user.id if user else None)

    return render(request, 'user_details.html', {
        'myuser': user,
        'selected_restaurant': restaurant,
    })

#this provides restaurant details in json or html
def restaurant_details(request, id):
    restaurant = get_object_or_404(Restaurant, id=id)
    owner = restaurant.owner

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': restaurant.id,
            'name': restaurant.name,
            'location': restaurant.location,
            'description': restaurant.description,
             'phone_number': restaurant.phone_number,
            'owner': owner.id if owner else None,
            'menu': restaurant.menu.id if restaurant.menu else None,
            "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
            "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
            "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
        })
    return render(request, 'user_details.html', {
        'selected_restaurant': restaurant,
        'myuser': owner,
    })

def main(request):
#This builds auth0 context
    context = {
        "AUTH0_DOMAIN": settings.AUTH0_DOMAIN,
        "AUTH0_CLIENT_ID": settings.AUTH0_CLIENT_ID,
        "AUTH0_CALLBACK_URL": settings.AUTH0_CALLBACK_URL,
    }

    user_session = request.session.get('user')
#this makes sure that the user is logged in and the details from the login are there before proceeding
    if user_session:
        email = user_session.get('email')
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "username": user_session.get("name", email.split("@")[0]),
                'is_authenticated': True
            },
        )
    else:
        # fallback to authenticated user if using Django auth
        user = request.user if request.user.is_authenticated else None
#this provides the ability to search for restaurants by name
    query = request.GET.get('q', '')
    if query:
        restaurants_qs = Restaurant.objects.filter(name__icontains=query)
    else:
        restaurants_qs = Restaurant.objects.all()

    # Build nested structure: each restaurant with its menus, sections, foods, and allergies
    #this is the nested structure for restaurants, menus, sections, foods, and allergies
    restaurants = []
    for r in restaurants_qs:
        menus = []
        for m in r.menus.all():
            sections = []
            for s in m.sections.all():
                foods = []
                for f in s.food_set.all():
                    allergens = list(f.allergies.all())
                    food_dict = {
                        'id': f.id,
                        'name': f.name,
                        # `Food_Allergen.allergen` is plain text now, use it
                        # for both value and label.
                        'allergens': [
                            {
                                'value': a.allergen,
                                'label': a.allergen
                            } for a in allergens 
                        ],
                    }
                    foods.append(food_dict)
                section_dict = {
                    'id': s.id,
                    'title': s.title,
                    'foods': foods,
                }
                sections.append(section_dict)
            menu_dict = {
                'id': m.id,
                'name': m.name,
                'sections': sections,
            }
            print(f"[DEBUG] Built Menu Dict: {menu_dict}")
            menus.append(menu_dict)
        restaurant_dict = {
            'id': r.id,
            'name': r.name,
            'location': r.location,
            'description': r.description,
            'phone_number': r.phone_number,
            'menus': menus,
        }
        print(f"[DEBUG] Built Restaurant Dict: {restaurant_dict}")
        restaurants.append(restaurant_dict)


        #THIS IS THE CORRECT ONE--DONT DELETE THIS COMMENT

    return render(request, 'user_details.html', {'myuser2': user, "allergies": Allergy.objects.all(), "restaurants": restaurants, **context})



#searches restaurants, what did you think it did? :)
def search_restaurants(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        restaurants = Restaurant.objects.filter(name__icontains=query)
        for r in restaurants:
            results.append({
                'id': r.id,
                'name': r.name,
                'location': r.location,
                'description': r.description,
                'phone_number': r.phone_number,
            })
    return JsonResponse({'results': results})
