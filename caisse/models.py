
from django.db import models
from django.utils import timezone

class Membre(models.Model):
    nom = models.CharField(max_length=150, verbose_name="Nom complet")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    date_inscription = models.DateField(default=timezone.now)

    def __str__(self):
        return self.nom

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('VERSEMENT', 'Versement (Cotisation)'),
        ('RETRAIT', 'Retrait (Aide accordée)'),
    ]
    
    MOIS_CHOICES = [
        ('01', 'Janvier'), ('02', 'Février'), ('03', 'Mars'), ('04', 'Avril'),
        ('05', 'Mai'), ('06', 'Juin'), ('07', 'Juillet'), ('08', 'Août'),
        ('09', 'Septembre'), ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre'),
    ]

    type_transaction = models.CharField(max_length=10, choices=TYPE_CHOICES, default='VERSEMENT')
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, null=True, blank=True, related_name='transactions', verbose_name="Membre (si versement)")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (MRU)")
    date_creation = models.DateTimeField(default=timezone.now)
    
    # Pour la flexibilité des mois/années cotisés
    annee_concernee = models.IntegerField(null=True, blank=True, verbose_name="Année concernée")
    # On stocke les mois sous forme de texte séparé par des virgules (ex: "01,02,03" pour 3 mois)
    mois_couverts = models.CharField(max_length=100, blank=True, null=True, verbose_name="Mois couverts (ex: Janvier, Février)")
    
    commentaire = models.TextField(blank=True, null=True, verbose_name="Détails / Bénéficiaire de l'aide")
    actif = models.BooleanField(default=True, verbose_name="Transaction active (incluse dans le total)")

    def __str__(self):
        if self.type_transaction == 'VERSEMENT':
            return f"Versement de {self.montant} MRU par {self.membre}"
        return f"Retrait (Aide) de {self.montant} MRU - {self.commentaire[:30]}"