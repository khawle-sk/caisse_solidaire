from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import MoisBudget, Cotisation, AideBeneficiaire

admin.site.register(MoisBudget)
admin.site.register(Cotisation)
admin.site.register(AideBeneficiaire)