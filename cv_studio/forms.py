import re
from django import forms
from django.core.exceptions import ValidationError
from .models import CV, Template


def parse_info_contact(info_contact):
    """Split serialized 'email | telephone | localisation' into a 3-tuple."""
    raw = (info_contact or '').strip()
    if not raw:
        return '', '', ''

    parts = [p.strip() for p in raw.split('|') if p.strip()]
    if len(parts) >= 3:
        return parts[0], parts[1], ' | '.join(parts[2:])
    if len(parts) == 2:
        email = parts[0] if '@' in parts[0] else ''
        if email:
            second_digits = re.sub(r'\D', '', parts[1])
            if len(second_digits) >= 6 and not any(ch.isalpha() for ch in parts[1]):
                return email, parts[1], ''
            return email, '', parts[1]
        return '', parts[0], parts[1]

    single = parts[0]
    if '@' in single:
        return single, '', ''
    if len(re.sub(r'\D', '', single)) >= 6 and not any(ch.isalpha() for ch in single):
        return '', single, ''
    return '', '', single


class CVForm(forms.ModelForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'input-email',
            'placeholder': 'nom@exemple.com',
        }),
        error_messages={'invalid': "Veuillez saisir une adresse email valide."},
    )
    telephone = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'input-phone',
            'placeholder': '+216 20 000 000',
        }),
    )
    localisation = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'input-location',
            'placeholder': 'Tunis, Tunisie',
        }),
    )

    class Meta:
        model = CV
        fields = [
            'template',
            'nom_document',
            'nom_complet',
            'titre_poste',
            'resume',
            'info_contact',
            'experience',
            'formation',
            'competences',
            'langues',
            'url_photo',
            'couleur_theme',
        ]
        widgets = {
            'template': forms.Select(attrs={'class': 'form-control', 'id': 'id_template'}),
            'nom_document': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'input-doc-name',
                'placeholder': 'ex: CV Ingénieur Full-Stack (auto si vide)',
            }),
            'nom_complet': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'input-name',
                'placeholder': 'Jean Dupont',
                'required': 'required',
            }),
            'titre_poste': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'input-title',
                'placeholder': 'ex: Développeur Full-Stack',
                'required': 'required',
            }),
            'resume': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'input-summary',
                'rows': 5,
                'maxlength': '1000',
                'placeholder': 'Présentez votre parcours, vos forces et vos objectifs...',
            }),
            'info_contact': forms.HiddenInput(attrs={'id': 'input-info-contact'}),
            'experience': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'input-experience',
                'rows': 4,
                'style': 'display:none;',
            }),
            'formation': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'input-education',
                'rows': 3,
                'style': 'display:none;',
            }),
            'competences': forms.HiddenInput(attrs={'id': 'input-skills'}),
            'langues': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'input-languages',
                'rows': 3,
                'style': 'display:none;',
            }),
            'url_photo': forms.HiddenInput(attrs={'id': 'photo-b64'}),
            'couleur_theme': forms.TextInput(attrs={
                'type': 'color',
                'class': 'color-picker',
                'id': 'color-picker',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nom_document'].required = False
        self.fields['titre_poste'].required = True
        self.fields['template'].required = False
        self.fields['info_contact'].required = False
        self.fields['url_photo'].required = False
        self.fields['couleur_theme'].required = False

        if not self.is_bound:
            if self.instance and self.instance.pk:
                email, phone, location = parse_info_contact(self.instance.info_contact)
                if email:
                    self.initial.setdefault('email', email)
                if phone:
                    self.initial.setdefault('telephone', phone)
                if location:
                    self.initial.setdefault('localisation', location)
                self.initial['couleur_theme'] = self.instance.couleur_theme or '#6b34a3'
            else:
                self.initial.setdefault('couleur_theme', '#6b34a3')

    def clean_nom_document(self):
        nom = (self.cleaned_data.get('nom_document') or '').strip()
        if nom and len(nom) < 3:
            raise ValidationError("Le nom du document doit comporter au moins 3 caractères.")
        if len(nom) > 150:
            raise ValidationError("Le nom du document ne peut pas dépasser 150 caractères.")
        return nom

    def clean_nom_complet(self):
        nom = (self.cleaned_data.get('nom_complet') or '').strip()
        if len(nom) < 3:
            raise ValidationError("Le nom complet doit comporter au moins 3 caractères.")
        return nom

    def clean_titre_poste(self):
        titre = (self.cleaned_data.get('titre_poste') or '').strip()
        if len(titre) < 2:
            raise ValidationError("Le titre du poste doit comporter au moins 2 caractères.")
        if len(titre) > 120:
            raise ValidationError("Le titre du poste ne peut pas dépasser 120 caractères.")
        return titre

    def clean_telephone(self):
        phone = (self.cleaned_data.get('telephone') or '').strip()
        if phone:
            digits = re.sub(r'\D', '', phone)
            if len(digits) < 8 or len(digits) > 20:
                raise ValidationError("Le numéro de téléphone doit contenir entre 8 et 20 chiffres.")
        return phone

    def clean_resume(self):
        resume = (self.cleaned_data.get('resume') or '').strip()
        plain = re.sub(r'<[^>]+>', '', resume).strip()
        if len(plain) > 1000:
            raise ValidationError("Le résumé professionnel ne peut pas dépasser 1000 caractères.")
        return resume

    def clean_couleur_theme(self):
        color = (self.cleaned_data.get('couleur_theme') or '').strip()
        if not color:
            return '#6b34a3'
        if not re.match(r'^#[0-9a-fA-F]{6}$', color):
            raise ValidationError("Couleur du thème invalide (format hexadécimal #RRGGBB attendu).")
        return color.lower()

    def clean(self):
        cleaned = super().clean()

        nom_complet = (cleaned.get('nom_complet') or '').strip()
        nom_document = (cleaned.get('nom_document') or '').strip()
        if not nom_document and nom_complet:
            cleaned['nom_document'] = f"CV {nom_complet}"[:150]

        email = (cleaned.get('email') or '').strip()
        telephone = (cleaned.get('telephone') or '').strip()
        localisation = (cleaned.get('localisation') or '').strip()
        raw_contact = (cleaned.get('info_contact') or '').strip()

        if email or telephone or localisation:
            if not email:
                self.add_error('email', "Veuillez saisir une adresse email valide.")
            cleaned['info_contact'] = ' | '.join([p for p in [email, telephone, localisation] if p])
        elif raw_contact:
            if '@' not in raw_contact and not re.search(r'\d{8,}', raw_contact):
                self.add_error('email', "Veuillez inclure une adresse email valide ou un numéro de téléphone.")
        else:
            self.add_error('email', "Veuillez saisir votre adresse email de contact.")

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.info_contact = self.cleaned_data.get('info_contact', '')
        instance.nom_document = self.cleaned_data.get('nom_document', instance.nom_document)
        instance.couleur_theme = self.cleaned_data.get('couleur_theme') or '#6b34a3'
        if commit:
            instance.save()
        return instance


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
