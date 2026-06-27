from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import MoisBudget, Cotisation, AideBeneficiaire
from django.db.models import Sum
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@login_required(login_url='login')
def home(request):
    mois_actif = MoisBudget.objects.filter(est_cloture=False).first()
    cotisations = []
    total_dons = 0
    aide = None

    if mois_actif:
        cotisations = mois_actif.cotisations.all().order_by('-id')
        total_dons = cotisations.aggregate(Sum('montant'))['montant__sum'] or 0
        aide = getattr(mois_actif, 'aide', None)

    mois_passes = MoisBudget.objects.filter(est_cloture=True).select_related('aide').order_by('-cree_le')

    context = {
        'mois_actif': mois_actif,
        'cotisations': cotisations,
        'total_dons': total_dons,
        'aide': aide,
        'mois_passes': mois_passes,
    }
    return render(request, 'index.html', context)

# 1. Créer le mois depuis le site
@login_required(login_url='login')
def CreerMois(request):
    if request.method == 'POST':
        nom_mois = request.POST.get('nom_mois')
        if not MoisBudget.objects.filter(est_cloture=False).exists():
            MoisBudget.objects.create(nom=nom_mois)
    return redirect('home')

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