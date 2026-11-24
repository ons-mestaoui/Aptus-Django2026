from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import RapportMarche, ReferenceRapport


TUNISIAN_GOVERNORATES = [
    'Tunis', 'Ariana', 'Ben Arous', 'Manouba',
    'Nabeul', 'Zaghouan', 'Bizerte',
    'Béja', 'Jendouba', 'Le Kef', 'Siliana',
    'Sousse', 'Monastir', 'Mahdia', 'Sfax',
    'Kairouan', 'Kasserine', 'Sidi Bouzid',
    'Gabès', 'Médenine', 'Tataouine',
    'Gafsa', 'Tozeur', 'Kébili',
]

BASE_REGION_CHOICES = (
    [('', '— Sélectionner une région —')]
    + [(gov, gov) for gov in TUNISIAN_GOVERNORATES]
    + [
        ('National (Tunisie)', 'National (Tunisie)'),
        ('International', 'International'),
        ('Global', 'Global'),
    ]
)

BASE_TENDANCE_CHOICES = [
    ('', '— Sélectionner une tendance —'),
    ('En hausse', 'En hausse'),
    ('Stable', 'Stable'),
    ('En baisse', 'En baisse'),
]

BASE_DEMANDE_CHOICES = [
    ('', '— Niveau de demande —'),
    (1, '1 — Faible'),
    (2, '2 — Modéré'),
    (3, '3 — Élevé'),
    (4, '4 — Très élevé / Critique'),
]


def _with_custom_choice(choices, current_value, label_fn=None):
    """Preserve an existing custom DB value in a select widget on edit."""
    if current_value in (None, ''):
        return list(choices)
    existing_values = {str(val) for val, _ in choices if val not in (None, '')}
    if str(current_value) in existing_values:
        return list(choices)
    label = label_fn(current_value) if label_fn else str(current_value)
    return [choices[0], (current_value, label)] + list(choices[1:])


class RapportMarcheForm(forms.ModelForm):
    class Meta:
        model = RapportMarche
        fields = [
            'titre', 'description', 'contenu_detaille', 'image_couverture',
            'date_publication', 'region', 'secteur_principal',
            'salaire_moyen_global', 'salaire_min_global', 'salaire_max_global',
            'tendance_generale', 'niveau_demande_global', 'auteur',
        ]
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du rapport'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Résumé exécutif du rapport de veille...'}),
            'contenu_detaille': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Analyse détaillée, méthodologie, constats et recommandations...'}),
            'image_couverture': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://... ou importez une image locale'}),
            'date_publication': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'secteur_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Data & IA, Tech & IT'}),
            'salaire_moyen_global': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Calculé auto si laissé vide'}),
            'salaire_min_global': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: 1800'}),
            'salaire_max_global': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Ex: 4500'}),
            'tendance_generale': forms.Select(attrs={'class': 'form-select'}),
            'niveau_demande_global': forms.Select(attrs={'class': 'form-select'}),
            'auteur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom de l'analyste"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_publication'].input_formats = ['%Y-%m-%d']
        if not self.instance.pk and not self.initial.get('date_publication'):
            self.initial['date_publication'] = timezone.localdate()

        self.fields['region'].widget.choices = _with_custom_choice(
            BASE_REGION_CHOICES, getattr(self.instance, 'region', None)
        )
        self.fields['tendance_generale'].widget.choices = _with_custom_choice(
            BASE_TENDANCE_CHOICES, getattr(self.instance, 'tendance_generale', None)
        )
        self.fields['niveau_demande_global'].widget.choices = _with_custom_choice(
            BASE_DEMANDE_CHOICES,
            getattr(self.instance, 'niveau_demande_global', None),
            label_fn=lambda v: f"{v} (Personnalisé)",
        )

    def clean_titre(self):
        titre = (self.cleaned_data.get('titre') or '').strip()
        if len(titre) < 3:
            raise ValidationError("Le titre du rapport doit contenir au moins 3 caractères.")
        return titre

    def clean(self):
        cleaned_data = super().clean()
        sal_min = cleaned_data.get('salaire_min_global')
        sal_max = cleaned_data.get('salaire_max_global')
        sal_moy = cleaned_data.get('salaire_moyen_global')

        for val in (sal_min, sal_max, sal_moy):
            if val is not None and val < 0:
                raise ValidationError("Les montants salariaux ne peuvent pas être négatifs.")

        if sal_min is not None and sal_max is not None and sal_min > sal_max:
            raise ValidationError("Le salaire minimum global ne peut pas être supérieur au salaire maximum global.")

        if sal_moy is None and sal_min is not None and sal_max is not None:
            cleaned_data['salaire_moyen_global'] = round((sal_min + sal_max) / 2, 2)

        return cleaned_data


class ReferenceRapportForm(forms.ModelForm):
    class Meta:
        model = ReferenceRapport
        fields = ['titre_source', 'url_source', 'note_source']
        widgets = {
            'titre_source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: INS Tunisie — Enquête Emploi 2026',
            }),
            'url_source': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://... (optionnel)',
            }),
            'note_source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Précision, date consultée, méthodologie... (optionnel)',
            }),
        }


ReferenceRapportFormSet = inlineformset_factory(
    RapportMarche,
    ReferenceRapport,
    form=ReferenceRapportForm,
    extra=1,
    can_delete=True,
)
