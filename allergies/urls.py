from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('allergies/',views.allergies, name='allergies'),
    path('allergies/details/<int:id>', views.details, name='details')
]