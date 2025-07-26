from allergies.models import Allergy
from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("restaurant", "Restaurant"),
        ("allergist", "Allergist"),
        ("patient", "Patient"),
    
    ]
    allergies= models.ManyToManyField(Allergy)


    role = models.CharField(choices= ROLE_CHOICES, max_length=255)


class Food_Allergen(models.Model):
    allergy_name = models.CharField(max_length = 255)

class Food(models.Model):
    name =  models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    allergies = models.ManyToManyField(Food_Allergen)

    


    
    
    
