from django import forms
from django.core.exceptions import ValidationError
from .models import Utilisateur, Candidat, Entreprise, Profil

class UtilisateurForm(forms.ModelForm):
    mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe (min. 8 car.)'}),
        required=False,
        help_text="Laissez vide pour conserver le mot de passe actuel lors d'une modification."
    )

    class Meta:
        model = Utilisateur
        fields = ['nom', 'prenom', 'email', 'mot_de_passe', 'role', 'telephone']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+216 ...'}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError("L'adresse email est obligatoire.")
        qs = Utilisateur.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Cette adresse email est déjà utilisée par un autre compte.")
        return email

    def clean_mot_de_passe(self):
        pwd = (self.cleaned_data.get('mot_de_passe') or '').strip()
        # Si création d'un nouvel utilisateur, le mot de passe est obligatoire
        if not self.instance.pk and not pwd:
            raise ValidationError("Le mot de passe est obligatoire lors de la création d'un utilisateur.")
        if pwd and len(pwd) < 8:
            raise ValidationError("Le mot de passe doit comporter au moins 8 caractères.")
        return pwd

class CandidatForm(forms.ModelForm):
    class Meta:
        model = Candidat
        fields = ['competences', 'niveau_etudes', 'niveau']
        widgets = {
            'competences': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Compétences clés...'}),
            'niveau_etudes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Bac+5 Ingénieur'}),
            'niveau': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Junior / Confirmé / Senior'}),
        }

class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ['raison_sociale', 'secteur', 'siret']
        widgets = {
            'raison_sociale': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'entreprise'}),
            'secteur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Informatique, Santé'}),
            'siret': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro SIRET (14 chiffres)'}),
        }

class ProfilForm(forms.ModelForm):
    class Meta:
        model = Profil
        fields = ['photo', 'bio', 'adresse', 'ville', 'pays', 'date_naissance', 'linkedin', 'site_web']
        widgets = {
            'photo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL ou nom du fichier photo'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Courte biographie...'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/...'}),
            'site_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }
