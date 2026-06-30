from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.core.paginator import Paginator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Transaction

# 🔥 SANS @login_required : Tout le monde peut voir la page d'accueil
def home(request):
    # 1. Calcul du solde dynamique global
    total_versements = Transaction.objects.filter(type_transaction='VERSEMENT', actif=True).aggregate(Sum('montant'))['montant__sum'] or 0
    total_retraits = Transaction.objects.filter(type_transaction='RETRAIT', actif=True).aggregate(Sum('montant'))['montant__sum'] or 0
    solde_caisse = total_versements - total_retraits

    # 2. Séparation des flux de base
    versements_list = Transaction.objects.filter(type_transaction='VERSEMENT', actif=True).order_by('-date_creation')
    retraits_list = Transaction.objects.filter(type_transaction='RETRAIT', actif=True).order_by('-date_creation')
    
    # 3. Récupération des filtres par section distincte
    query_nom_v = request.GET.get('nom_v', '').strip()
    query_mois = request.GET.get('mois', '').strip()
    query_annee_v = request.GET.get('annee_v', '').strip()

    query_nom_r = request.GET.get('nom_r', '').strip()
    query_annee_r = request.GET.get('annee_r', '').strip()

    # Application des filtres sur les Cotisations (Section Donateurs)
    if query_nom_v:
        versements_list = versements_list.filter(commentaire__icontains=query_nom_v)
    if query_mois:
        nom_mois_clair = dict(Transaction.MOIS_CHOICES).get(query_mois, query_mois)
        versements_list = versements_list.filter(mois_couverts__icontains=nom_mois_clair)
    if query_annee_v:
        versements_list = versements_list.filter(annee_concernee=query_annee_v)

    # Application des filtres sur les Aides (Section Bénéficiaires)
    if query_nom_r:
        retraits_list = retraits_list.filter(commentaire__icontains=query_nom_r)
    if query_annee_r:
        retraits_list = retraits_list.filter(date_creation__year=query_annee_r)

    # 4. Doubles Paginations Indépendantes
    page_versements = request.GET.get('page_v', 1)
    paginator_v = Paginator(versements_list, 15)
    page_obj_v = paginator_v.get_page(page_versements)

    page_retraits = request.GET.get('page_r', 1)
    paginator_r = Paginator(retraits_list, 15)
    page_obj_r = paginator_r.get_page(page_retraits)

    # Variables d'édition (uniquement si l'utilisateur est authentifié pour éviter des bugs)
    edit_transaction = None
    edit_id = request.GET.get('edit_id')
    if edit_id and request.user.is_authenticated:
        edit_transaction = get_object_or_404(Transaction, id=edit_id, actif=True)

    context = {
        'solde_caisse': solde_caisse,
        'page_obj_v': page_obj_v,
        'page_obj_r': page_obj_r,
        'mois_choices': Transaction.MOIS_CHOICES,
        'query_nom_v': query_nom_v,
        'query_nom_r': query_nom_r,
        'query_mois': query_mois,
        'query_annee_v': query_annee_v,
        'query_annee_r': query_annee_r,
        'edit_transaction': edit_transaction,
    }
    return render(request, 'index.html', context)

@login_required(login_url='login')
def AjouterDon(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        nom_donateur = request.POST.get('nom_donateur', '').strip()
        annee = request.POST.get('annee')
        mois_list = request.POST.getlist('mois_selectionnes')
        
        if nom_donateur and mois_list:
            nb_mois = len(mois_list)
            montant_calcule = nb_mois * 100
            mois_string = ", ".join([dict(Transaction.MOIS_CHOICES).get(m, m) for m in mois_list])
            
            if transaction_id:
                t = get_object_or_404(Transaction, id=transaction_id, type_transaction='VERSEMENT')
                t.montant = montant_calcule
                t.annee_concernee = annee if annee else None
                t.mois_couverts = mois_string
                t.commentaire = f"Donateur: {nom_donateur}"
                t.save()
            else:
                Transaction.objects.create(
                    type_transaction='VERSEMENT',
                    montant=montant_calcule,
                    annee_concernee=annee if annee else None,
                    mois_couverts=mois_string,
                    commentaire=f"Donateur: {nom_donateur}",
                    actif=True
                )
    return redirect('home')

@login_required(login_url='login')
def EnregistrerAide(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        beneficiaire = request.POST.get('nom', '').strip()
        montant = request.POST.get('montant')
        cause = request.POST.get('cause', '').strip()
        
        if beneficiaire and montant:
            if transaction_id:
                t = get_object_or_404(Transaction, id=transaction_id, type_transaction='RETRAIT')
                t.montant = montant
                t.commentaire = f"Bénéficiaire: {beneficiaire} | Cause: {cause}"
                t.save()
            else:
                Transaction.objects.create(
                    type_transaction='RETRAIT',
                    montant=montant,
                    commentaire=f"Bénéficiaire: {beneficiaire} | Cause: {cause}",
                    actif=True
                )
    return redirect('home')

@login_required(login_url='login')
def ConfirmerSuppression(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, actif=True)
    if request.method == 'POST':
        transaction.delete()
        return redirect('home')
    return render(request, 'confirmer_suppression.html', {'transaction': transaction})

@login_required(login_url='login')
def TelechargerPDF(request, transaction_id):
    aide = get_object_or_404(Transaction, id=transaction_id, type_transaction='RETRAIT')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=\"Recu_Aide_{transaction_id}.pdf\"'
    
    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, "RECU D'AIDE HUMANITAIRE - CAISSE SOLIDAIRE")
    p.line(100, 730, 500, 730)
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 680, f"Numéro de reçu : #{aide.id}")
    p.drawString(100, 650, f"{aide.commentaire}")
    p.drawString(100, 620, f"Montant Total Déduit : {aide.montant} MRU")
    
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, 500, f"Document officiel généré le : {aide.date_creation.strftime('%d/%m/%Y à %H:%M')}")
    
    p.showPage()
    p.save()
    return response