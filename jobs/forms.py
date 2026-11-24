from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import OffreEmploi, Candidature

class OffreEmploiForm(forms.ModelForm):
    class Meta:
        model = OffreEmploi
        fields = ['entreprise', 'titre', 'description', 'competences_requises', 'salaire', 'date_expir', 'domaine', 'experience_requise', 'question']
        widgets = {
            'entreprise': forms.Select(attrs={'class': 'form-select'}),
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de l\'offre'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description du poste...'}),
            'competences_requises': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Python, Django, React, SQL...'}),
            'salaire': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'ex: 45000'}),
            'date_expir': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'domaine': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Informatique / IT'}),
            'experience_requise': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: 2 ans'}),
            'question': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Question personnalisée pour le candidat'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_expir'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        if self.instance and self.instance.pk:
            candidates = [d for d in (self.instance.date_publication, self.instance.date_expir) if d is not None]
            min_date = min(candidates) if candidates else date.today()
        else:
            min_date = date.today()
        self.fields['date_expir'].widget.attrs['min'] = min_date.isoformat()

    def clean_titre(self):
        titre = (self.cleaned_data.get('titre') or '').strip()
        if len(titre) < 3:
            raise ValidationError("Le titre doit contenir au moins 3 caractères.")
        return titre

    def clean_salaire(self):
        salaire = self.cleaned_data.get('salaire')
        if salaire is not None and salaire <= 0:
            raise ValidationError("Le salaire doit être un montant positif.")
        return salaire

    def clean_question(self):
        question = (self.cleaned_data.get('question') or '').strip()
        if not question:
            raise ValidationError("Veuillez poser une question pour filtrer vos candidats.")
        return question

    def clean_date_expir(self):
        date_expir = self.cleaned_data.get('date_expir')
        if date_expir:
            if self.instance and self.instance.pk and date_expir == self.instance.date_expir:
                return date_expir
            # Vérifie que la date d'expiration n'est pas antérieure à la date de publication
            # (si une date de publication existe sur l'instance, sinon date.today())
            ref_date = date.today()
            if self.instance and self.instance.pk and self.instance.date_publication:
                ref_date = self.instance.date_publication
            if date_expir < ref_date:
                raise ValidationError("La date d'expiration ne peut pas être antérieure à la date de publication.")
        return date_expir


class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['candidat', 'offre', 'reponses_ques', 'cv_cand', 'note', 'statut']
        widgets = {
            'candidat': forms.Select(attrs={'class': 'form-select'}),
            'offre': forms.Select(attrs={'class': 'form-select'}),
            'reponses_ques': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Développez votre réponse (min. 10 caractères)...'}),
            'note': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Note ou score IA (ex: 85)'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_reponses_ques(self):
        reponses = (self.cleaned_data.get('reponses_ques') or '').strip()
        if not reponses:
            raise ValidationError("La réponse à la question de l'entreprise est obligatoire.")
        if len(reponses) < 10:
            raise ValidationError("La réponse doit comporter au moins 10 caractères.")
        return reponses
