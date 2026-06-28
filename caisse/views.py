from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Membre, Transaction
from django.db.models import Sum
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect

from django.core.paginator import Paginator


@login_required(login_url='login')
def home(request):
    # 1. Calcul du solde total dynamique de la caisse (Transactions actives uniquement)
    total_versements = Transaction.objects.filter(type_transaction='VERSEMENT', actif=True).aggregate(Sum('montant'))['montant__sum'] or 0
    total_retraits = Transaction.objects.filter(type_transaction='RETRAIT', actif=True).aggregate(Sum('montant'))['montant__sum'] or 0
    solde_caisse = total_versements - total_retraits

    # 2. Récupération de toutes les transactions actives
    transactions_list = Transaction.objects.filter(actif=True).order_by('-date_creation')
    
    # 3. Système de RECHERCHE MULTI-CRITÈRES SIMULTANÉS
    query_nom = request.GET.get('nom', '').strip()
    query_mois = request.GET.get('mois', '').strip()
    query_annee = request.GET.get('annee', '').strip()

    if query_nom:
        # Recherche par le nom du membre (insensible à la casse)
        transactions_list = transactions_list.filter(membre__nom__icontains=query_nom)
    if query_mois:
        # Recherche si le mois est inclus dans la liste des mois couverts
        transactions_list = transactions_list.filter(mois_couverts__icontains=query_mois)
    if query_annee:
        # Recherche par année exacte
        transactions_list = transactions_list.filter(annee_concernee=query_annee)

    # 4. Système de PAGINATION (15 transactions par page)
    paginator = Paginator(transactions_list, 15)
    page_number = request.get_full_path().split('page=')[-1] if 'page=' in request.get_full_path() else 1
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'solde_caisse': solde_caisse,
        'page_obj': page_obj,             # Contient les 15 transactions de la page courante
        'mois_choices': Transaction.MOIS_CHOICES, # Pour afficher la liste dans le select du filtre
        # On renvoie les valeurs pour garder les filtres affichés à l'écran après la recherche
        'query_nom': query_nom,
        'query_mois': query_mois,
        'query_annee': query_annee,
    }
    return render(request, 'caisse/home.html', context)

# 2. NOUVEAU : Ajouter un don depuis le site
@login_required(login_url='login')
def AjouterDon(request, mois_id):
    mois = get_object_or_404(MoisBudget, id=mois_id)
    if request.method == 'POST' and not mois.est_cloture:
        nom = request.POST.get('nom_donateur')
        montant = request.POST.get('montant')
        if nom and montant:
            Cotisation.objects.create(mois=mois, nom_donateur=nom, montant=montant)
    return redirect('home')

# 3. Clôturer et faire le PDF depuis le site
@login_required(login_url='login')
def EnregistrerAide(request, mois_id):
    mois = get_object_or_404(MoisBudget, id=mois_id)
    if request.method == 'POST':
        nom = request.POST.get('nom')
        montant = request.POST.get('montant')
        cause = request.POST.get('cause')
        
        AideBeneficiaire.objects.create(mois=mois, nom_beneficiaire=nom, montant_accorde=montant, cause=cause)
        mois.est_cloture = True
        mois.save()
        return redirect('home')

@login_required(login_url='login')
def TelechargerPDF(request, aide_id):
    aide = get_object_or_404(AideBeneficiaire, id=aide_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Aide_{aide.nom_beneficiaire}.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, f"RECU D'AIDE HUMANITAIRE - {aide.mois.nom}")
    p.line(100, 730, 500, 730)
    
    p.setFont("Helvetica", 14)
    p.drawString(100, 680, f"Bénéficiaire : {aide.nom_beneficiaire}")
    p.drawString(100, 650, f"Montant Total Accordé : {aide.montant_accorde} €")
    p.drawString(100, 620, f"Raison / Description :")
    p.drawString(100, 600, f"{aide.cause}")
    
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, 500, f"Document généré le : {aide.cree_le.strftime('%d/%m/%Y')}")
    
    p.showPage()
    p.save()
    return response