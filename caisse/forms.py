from django import forms
from .models import Transaction, Membre

class TransactionForm(forms.ModelForm):
    # Champ personnalisé pour afficher les mois sous forme de cases à cocher
    mois_selectionnes = forms.MultipleChoiceField(
        choices=Transaction.MOIS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Sélectionnez le ou les mois concernés"
    )

    class Meta:
        model = Transaction
        fields = ['type_transaction', 'membre', 'montant', 'annee_concernee', 'commentaire', 'actif']

    def save(self, commit=True):
        instance = super().save(commit=False)
        # On convertit la liste des mois cochés en chaîne de caractères séparée par des virgules
        mois_list = self.cleaned_data.get('mois_selectionnes')
        if mois_list:
            instance.mois_couverts = ",".join(mois_list)
        if commit:
            instance.save()
        return instance