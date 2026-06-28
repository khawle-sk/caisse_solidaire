from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.core.paginator import Paginator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Membre, Transaction

@login_required(login_url='login')
def home(request):
    # 1. Calcul du solde dynamique de la caisse
    total_versements = Transaction.objects.filter(type_transaction='VERSEMENT', actif=True).aggregate(Sum('montant'))['montant__sum'] or 0
    total_retraits = Transaction.objects.filter(type_transaction='RETRAIT', actif=True).aggregate(Sum('montant'))['montant__sum'] or 0
    solde_caisse = total_versements - total_retraits

    # 2. Récupération des transactions
    transactions_list = Transaction.objects.filter(actif=True).order_by('-date_creation')
    
    # 3. Système de filtres cumulatifs simultanés
    query_nom = request.GET.get('nom', '').strip()
    query_mois = request.GET.get('mois', '').strip()
    query_annee = request.GET.get('annee', '').strip()

    if query_nom:
        transactions_list = transactions_list.filter(membre__nom__icontains=query_nom)
    if query_mois:
        transactions_list = transactions_list.filter(mois_couverts__icontains=query_mois)
    if query_annee:
        transactions_list = transactions_list.filter(annee_concernee=query_annee)

    # 4. Pagination (15 par page)
    paginator = Paginator(transactions_list, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Liste des membres pour le menu déroulant
    membres = Membre.objects.all().order_by('nom')

    context = {
        'solde_caisse': solde_caisse,
        'page_obj': page_obj,
        'mois_choices': Transaction.MOIS_CHOICES,
        'membres': membres,
        'query_nom': query_nom,
        'query_mois': query_mois,
        'query_annee': query_annee,
    }
    return render(request, 'index.html', context)

@login_required(login_url='login')
def AjouterDon(request):
    if request.method == 'POST':
        membre_id = request.POST.get('membre_id')
        montant = request.POST.get('montant')
        annee = request.POST.get('annee')
        mois_list = request.POST.getlist('mois_selectionnes')
        
        if membre_id and montant:
            membre = get_object_or_404(Membre, id=membre_id)
            # Conversion de la liste des mois cochés en texte séparé par des virgules
            mois_string = ", ".join([dict(Transaction.MOIS_CHOICES).get(m, m) for m in mois_list]) if mois_list else ""
            
            Transaction.objects.create(
                type_transaction='VERSEMENT',
                membre=membre,
                montant=montant,
                annee_concernee=annee if annee else None,
                mois_couverts=mois_string,
                actif=True
            )
    return redirect('home')

@login_required(login_url='login')
def EnregistrerAide(request):
    if request.method == 'POST':
        beneficiaire = request.POST.get('nom')
        montant = request.POST.get('montant')
        cause = request.POST.get('cause')
        
        if beneficiaire and montant:
            Transaction.objects.create(
                type_transaction='RETRAIT',
                montant=montant,
                commentaire=f"Bénéficiaire: {beneficiaire} | Cause: {cause}",
                actif=True
            )
    return redirect('home')

@login_required(login_url='login')
def TelechargerPDF(request, transaction_id):
    aide = get_object_or_404(Transaction, id=transaction_id, type_transaction='RETRAIT')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Recu_Aide_{transaction_id}.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, "RECU D'AIDE HUMANITAIRE - CAISSE SOLIDAIRE")
    p.line(100, 730, 500, 730)
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 680, f"Numéro de reçu : #{aide.id}")
    p.drawString(100, 650, f"Détails : {aide.commentaire}")
    p.drawString(100, 620, f"Montant Total Retiré : {aide.montant} MRU")
    
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, 500, f"Document officiel généré le : {aide.date_creation.strftime('%d/%m/%Y à %H:%M')}")
    
    p.showPage()
    p.save()
    return response