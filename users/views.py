from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .models import CustomUser
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote_plus, urlencode
import json
from authlib.integrations.django_client import OAuth

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
            name = data.get('name')
            restaurant_id = data.get('restaurant')
            section_ids = data.get('sections', [])

            restaurant = Restaurant.objects.get(id=restaurant_id)
            new_menu = Menu.objects.create(
                name=name,
                restaurant=restaurant,
            )
            new_menu.sections.set(Menu_Section.objects.filter(id__in=section_ids))
            user.menus.add(new_menu)

            return JsonResponse({'status': 'created', 'Menu_id': new_menu.id}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)


   if request.GET.get('search'):
      queryset = queryset.filter(name__icontains=request.GET.get('search'))

   context = {
      'my_menus':queryset, 'myuser':user
   }   
   return render(request, 'user_details.html', context)

def delete_menu(request, id):
   menu = get_object_or_404(Menu, id=id)
   user = menu.customuser_set.first()
   user.menus.remove(menu)
   return redirect('user_details', user_id=user.id)

def update_menu(request, id):
    menu = get_object_or_404(Menu, id=id)
    user = menu.customuser_set.first()

    if request.method == 'POST':
        name = request.POST.get('name')
        restaurant_id = request.POST.get('restaurant')
        section_ids = request.POST.getlist('sections')  # Use getlist for multiple values

        menu.name = name
        menu.restaurant = Restaurant.objects.get(id=restaurant_id)
        menu.save()
        menu.sections.set(Menu_Section.objects.filter(id__in=section_ids))
        return redirect('user_details', user_id=user.id)

    menus = user.menus.all()
    return render(request, 'user_details.html', {'myuser': user, 'menus': menus, 'selected_menu': menu})


def details(request, id):
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
  template = loader.get_template('user_details.html')
  return HttpResponse(template.render())
