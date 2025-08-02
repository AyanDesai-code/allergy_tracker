from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('allergies/details/<int:id>', views.details, name='details'),
    path('<int:user_id>/', views.allergies, name='allergies'),
]