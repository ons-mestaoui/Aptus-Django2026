from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Formation, Inscription

class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        fields = ['titre', 'description', 'domaine', 'niveau', 'date_formation', 'tuteur', 'is_online', 'lien_api_room']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la formation'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description détaillée des objectifs pédagogiques...'}),
            'domaine': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Data Science, Web, Cloud'}),
            'niveau': forms.Select(attrs={'class': 'form-select'}),
            'date_formation': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tuteur': forms.Select(attrs={'class': 'form-select'}),
            'is_online': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'lien_api_room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://meet...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now_str = timezone.now().strftime('%Y-%m-%dT%H:%M')
        self.fields['date_formation'].widget.attrs['min'] = now_str

    def clean_titre(self):
        titre = (self.cleaned_data.get('titre') or '').strip()
        if len(titre) < 3:
            raise ValidationError("Le titre de la formation doit comporter au moins 3 caractères.")
        return titre

    def clean_domaine(self):
        domaine = (self.cleaned_data.get('domaine') or '').strip()
        if len(domaine) < 2:
            raise ValidationError("Le domaine technique est requis.")
        return domaine

    def clean_date_formation(self):
        date_formation = self.cleaned_data.get('date_formation')
        if date_formation and date_formation < timezone.now():
            raise ValidationError("La date de la formation ne peut pas être planifiée dans le passé.")
        return date_formation


class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ['candidat', 'formation', 'statut', 'progression']
        widgets = {
            'candidat': forms.Select(attrs={'class': 'form-select'}),
            'formation': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'progression': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }
