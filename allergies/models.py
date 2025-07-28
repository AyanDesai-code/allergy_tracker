from django.db import models

# Create your models here.
class Allergy(models.Model):
    ALLERGY_CHOICES = [
        ("milk", "Milk"),
        ("eggs", "Eggs"),
        ("shellfish", "Shellfish"),
        ("treenuts", "Treenuts"),
        ("peanuts", "Peanuts"),
        ("wheat", "Wheat"),
        ("soybeans", "Soybeans"),
        ("sesame", "Sesame"),
        ("fish", "Fish"),
    
    ]
    
    allergyname = models.CharField(choices=ALLERGY_CHOICES, max_length=255, null=True)

    test_level = models.DecimalField(null=True, max_digits=10, decimal_places=2,)
    category = models.CharField(max_length=255, null=True) 

    def __str__(self):
        return self.name
    
