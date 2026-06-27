from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone

class MoisBudget(models.Model):
    """Représente un mois de collecte (ex: 'Juillet 2026')"""
    nom = models.CharField(max_length=50, verbose_name="Mois et Année (ex: Juillet 2026)")
    cree_le = models.DateTimeField(default=timezone.now)
    est_cloture = models.BooleanField(default=False, verbose_name="Mois clôturé ?")

    def __str__(self):
        statut = "Clôturé" if self.est_cloture else "En cours"
        return f"{self.nom} ({statut})"

class Cotisation(models.Model):
    """Table pour enregistrer l'argent qui rentre (les donateurs)"""
    mois = models.ForeignKey(MoisBudget, on_delete=models.CASCADE, related_name="cotisations")
    nom_donateur = models.CharField(max_length=100, verbose_name="Nom du donateur")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (€)")
    date_don = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.nom_donateur} - {self.montant}€"

class AideBeneficiaire(models.Model):
    """Table pour l'argent qui sort (génère le PDF)"""
    mois = models.OneToOneField(MoisBudget, on_delete=models.CASCADE, related_name="aide")
    nom_beneficiaire = models.CharField(max_length=100, verbose_name="Nom du bénéficiaire")
    montant_accorde = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant accordé (€)")
    cause = models.TextField(verbose_name="Cause de l'aide")
    cree_le = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Aide pour {self.nom_beneficiaire}"