import re
from django import forms
from django.core.exceptions import ValidationError
from .models import CV, Template, RapportIA

class CVForm(forms.ModelForm):
    class Meta:
        model = CV
        fields = ['candidat', 'template', 'nom_document', 'nom_complet', 'titre_poste', 'resume', 'info_contact', 'experience', 'formation', 'competences', 'langues', 'statut']
        widgets = {
            'candidat': forms.Select(attrs={'class': 'form-select'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'nom_document': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: CV Ingénieur IA'}),
            'nom_complet': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jean Dupont'}),
            'titre_poste': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Lead Data Scientist'}),
            'resume': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'info_contact': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Email, Téléphone, Adresse'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'formation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'competences': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'langues': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Français, Anglais'}),
            'statut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Actif / Brouillon'}),
        }

    def clean_nom_document(self):
        nom = (self.cleaned_data.get('nom_document') or '').strip()
        if len(nom) < 3:
            raise ValidationError("Le nom du document doit comporter au moins 3 caractères.")
        if len(nom) > 150:
            raise ValidationError("Le nom du document ne peut pas dépasser 150 caractères.")
        return nom

    def clean_nom_complet(self):
        nom = (self.cleaned_data.get('nom_complet') or '').strip()
        if len(nom) < 3:
            raise ValidationError("Le nom complet doit comporter au moins 3 caractères.")
        return nom

    def clean_info_contact(self):
        contact = (self.cleaned_data.get('info_contact') or '').strip()
        if contact:
            # Validation de format : doit comporter un email ou au moins 6 chiffres pour un numéro de téléphone
            if '@' not in contact and not re.search(r'\d{6,}', contact):
                raise ValidationError("Veuillez inclure une adresse email valide ou un numéro de téléphone dans vos coordonnées.")
        return contact

    def clean_titre_poste(self):
        titre = (self.cleaned_data.get('titre_poste') or '').strip()
        if titre and len(titre) < 2:
            raise ValidationError("Le titre du poste doit comporter au moins 2 caractères.")
        return titre


class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ['nom', 'description', 'url_miniature', 'structure_html', 'est_premium']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Élégance Corporative'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tags séparés par virgule'}),
            'url_miniature': forms.HiddenInput(attrs={'id': 'page-url-hidden'}),
            'structure_html': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 16,
                'placeholder': 'Écrivez le code source HTML/CSS du CV ici...',
                'style': 'font-family: Consolas, monospace; font-size: 13px; line-height: 1.5;'
            }),
            'est_premium': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'tpl-premium'}),
        }

    def clean_nom(self):
        nom = (self.cleaned_data.get('nom') or '').strip()
        if len(nom) < 3 or len(nom) > 150:
            raise ValidationError("Le nom du template doit contenir entre 3 et 150 caractères.")
        return nom

    def clean_structure_html(self):
        html = (self.cleaned_data.get('structure_html') or '').strip()
        if not html:
            raise ValidationError("Le code HTML du template est obligatoire.")
        if not re.search(r'<[a-z][\s\S]*>', html, re.IGNORECASE):
            raise ValidationError("Le code doit contenir des balises HTML valides (ex: <div>, <span>).")
        return html
