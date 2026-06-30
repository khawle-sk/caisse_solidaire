from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from caisse import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # Authentification personnalisée (Professionnelle)
    path('login/', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    
    # 🔥 CORRECTION : On redirige vers l'accueil ('home') après la déconnexion
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Actions de la caisse (Réservées aux admins via views.py)
    path('ajouter-don/', views.AjouterDon, name='ajouter_don'),
    path('enregistrer-aide/', views.EnregistrerAide, name='enregistrer_aide'),
    path('supprimer/<int:transaction_id>/', views.ConfirmerSuppression, name='confirmer_suppression'),
    path('pdf/<int:transaction_id>/', views.TelechargerPDF, name='telecharger_pdf'),
]