from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(LoanAdmin)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email' 'created_at', 'updated_at')
