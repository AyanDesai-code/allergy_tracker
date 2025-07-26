from django.db import models

# Create your models here.
class Allergy(models.Model):
    allergyname = models.CharField(max_length=255)
    test_level = models.DecimalField(null=True, max_digits=10, decimal_places=2,)
    category = models.CharField(max_length=255, null=True) 