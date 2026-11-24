from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Formation, Inscription
from accounts.models import Utilisateur

class FormationForm(forms.ModelForm):
    is_online = forms.ChoiceField(
        choices=[(False, '📍 Présentiel'), (True, '🌐 En ligne / Distanciel')],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_is_online'}),
        required=False,
        label="Format / Lieu"
    )

    class Meta:
        model = Formation
        fields = [
            'titre', 'description', 'domaine', 'niveau', 'duree',
            'date_formation', 'date_fin', 'tuteur', 'prerequis',
            'image', 'is_online', 'lien_api_room'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la formation'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'id': 'hidden-description', 'placeholder': 'Description détaillée en contenu riche...'}),
            'domaine': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Data Science, Web, Cloud'}),
            'niveau': forms.Select(attrs={'class': 'form-select'}),
            'duree': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: 10h'}),
            'date_formation': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'date_fin': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'tuteur': forms.Select(attrs={'class': 'form-select'}),
            'prerequis': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'lien_api_room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://meet.jit.si/aptus-room...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dt_formats = [
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y %H:%M:%S',
        ]
        self.fields['date_formation'].input_formats = dt_formats
        self.fields['date_fin'].input_formats = dt_formats

        now_local = timezone.localtime(timezone.now())
        if self.instance and self.instance.pk and self.instance.date_formation:
            existing_dt = self.instance.date_formation
            if timezone.is_aware(existing_dt):
                existing_dt = timezone.localtime(existing_dt)
            else:
                existing_dt = timezone.make_aware(existing_dt)
            min_dt = min(existing_dt, now_local)
        else:
            min_dt = now_local
        self.fields['date_formation'].widget.attrs['min'] = min_dt.strftime('%Y-%m-%dT%H:%M')
        # Filtrer les tuteurs disponibles (Tuteurs ou Admins)
        self.fields['tuteur'].queryset = Utilisateur.objects.filter(role__in=['Tuteur', 'Admin']).order_by('nom')
        self.fields['tuteur'].empty_label = "Sélectionnez un tuteur référent..."
        self.fields['prerequis'].empty_label = "Aucun prérequis"
        if self.instance and self.instance.pk:
            self.fields['prerequis'].queryset = Formation.objects.exclude(pk=self.instance.pk)
            # Boolean format convert
            self.initial['is_online'] = bool(self.instance.is_online)

    def clean_is_online(self):
        val = self.cleaned_data.get('is_online')
        return val in [True, 'True', '1', 1]

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

    @staticmethod
    def _same_minute(dt_a, dt_b):
        """Compare two datetimes at minute precision in the active local timezone."""
        a = timezone.localtime(dt_a) if timezone.is_aware(dt_a) else timezone.make_aware(dt_a)
        b = timezone.localtime(dt_b) if timezone.is_aware(dt_b) else timezone.make_aware(dt_b)
        return a.replace(second=0, microsecond=0) == b.replace(second=0, microsecond=0)

    def clean_date_formation(self):
        date_formation = self.cleaned_data.get('date_formation')
        if date_formation:
            if (
                self.instance
                and self.instance.pk
                and self.instance.date_formation
                and self._same_minute(date_formation, self.instance.date_formation)
            ):
                return self.instance.date_formation
            if date_formation < timezone.now():
                raise ValidationError("La date de la formation ne peut pas être planifiée dans le passé.")
        return date_formation

    def clean_date_fin(self):
        date_formation = self.cleaned_data.get('date_formation')
        date_fin = self.cleaned_data.get('date_fin')
        if date_fin:
            if (
                self.instance
                and self.instance.pk
                and self.instance.date_fin
                and self._same_minute(date_fin, self.instance.date_fin)
            ):
                date_fin = self.instance.date_fin
            if date_formation and date_fin <= date_formation:
                raise ValidationError("La date de fin doit être postérieure à la date de début de formation.")
        return date_fin

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("L'image de couverture ne doit pas dépasser 5 Mo.")
            # Validation du format d'image
            ext = (image.name or '').split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'avif']:
                raise ValidationError("Format d'image non supporté (formats acceptés : JPG, PNG, WEBP, AVIF).")
        return image



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
