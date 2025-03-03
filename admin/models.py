from django.db import models
from gigworkers.managers import *


# Create your models here.
class LoanAdmin(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='loan_admin')
    name = models.CharField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=10, validators=[validate_mobile_no])
    gender=models.CharField(null=True, blank=True, max_length=100)
    email=models.EmailField(max_length=255,null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
