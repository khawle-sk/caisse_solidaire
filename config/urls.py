from django.contrib import admin
from django.urls import path, include  # On ajoute 'include'
from caisse import views

urlpatterns = [
    # Route pour l'administration
    path('admin/', admin.site.urls),
    
    # 🌟 C'est CETTE ligne qui dit à Django d'afficher ton index.html AUTOMATIQUEMENT à la racine !
    path('', views.home, name='home'),
]