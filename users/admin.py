from django.contrib import admin
from .models import *


# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Restaurant)
admin.site.register(Menu)
admin.site.register(Menu_Section)
admin.site.register(Food)
admin.site.register(Food_Allergen)