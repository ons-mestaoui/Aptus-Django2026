from django import forms
from django.core.exceptions import ValidationError
from .models import RapportMarche, DonneeMarche

class RapportMarcheForm(forms.ModelForm):
    class Meta:
        model = RapportMarche
        fields = ['admin', 'titre', 'description', 'date_publication', 'region', 'secteur_principal', 'salaire_moyen_global', 'salaire_min_global', 'salaire_max_global', 'tendance_generale', 'niveau_demande_global', 'auteur']
        widgets = {
            'admin': forms.Select(attrs={'class': 'form-select'}),
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du rapport'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_publication': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Île-de-France, Tunisie, Global'}),
            'secteur_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Data & IA'}),
            'salaire_moyen_global': forms.NumberInput(attrs={'class': 'form-control'}),
            'salaire_min_global': forms.NumberInput(attrs={'class': 'form-control'}),
            'salaire_max_global': forms.NumberInput(attrs={'class': 'form-control'}),
            'tendance_generale': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'En hausse / Stable'}),
            'niveau_demande_global': forms.NumberInput(attrs={'class': 'form-control'}),
            'auteur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'analyste'}),
        }

    def clean_titre(self):
        titre = (self.cleaned_data.get('titre') or '').strip()
        if len(titre) < 3:
            raise ValidationError("Le titre du rapport doit contenir au moins 3 caractères.")
        return titre

    def clean(self):
        cleaned_data = super().clean()
        sal_min = cleaned_data.get('salaire_min_global')
        sal_max = cleaned_data.get('salaire_max_global')
        if sal_min is not None and sal_max is not None and sal_min > sal_max:
            raise ValidationError("Le salaire minimum global ne peut pas être supérieur au salaire maximum global.")
        return cleaned_data


class DonneeMarcheForm(forms.ModelForm):
    class Meta:
        model = DonneeMarche
        fields = ['rapport_marche', 'domaine', 'competence', 'salaire_min', 'salaire_max', 'salaire_moyen', 'demande', 'date_collecte']
        widgets = {
            'rapport_marche': forms.Select(attrs={'class': 'form-select'}),
            'domaine': forms.TextInput(attrs={'class': 'form-control'}),
            'competence': forms.TextInput(attrs={'class': 'form-control'}),
            'salaire_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'salaire_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'salaire_moyen': forms.NumberInput(attrs={'class': 'form-control'}),
            'demande': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_collecte': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        sal_min = cleaned_data.get('salaire_min')
        sal_max = cleaned_data.get('salaire_max')
        if sal_min is not None and sal_max is not None and sal_min > sal_max:
            raise ValidationError("Le salaire minimum ne peut pas être supérieur au salaire maximum.")
        return cleaned_data
