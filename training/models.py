from django.db import models
from accounts.models import Utilisateur, Candidat

class Formation(models.Model):
    NIVEAU_CHOICES = [
        ('Débutant', 'Débutant'),
        ('Intermédiaire', 'Intermédiaire'),
        ('Avancé', 'Avancé'),
        ('Expert', 'Expert'),
    ]

    id_formation = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    domaine = models.CharField(max_length=255, null=True, blank=True)
    niveau = models.CharField(max_length=50, choices=NIVEAU_CHOICES, default='Débutant')
    duree = models.CharField(max_length=50, null=True, blank=True, default='10h', verbose_name="Durée")
    date_formation = models.DateTimeField(null=True, blank=True, verbose_name="Date de début")
    date_fin = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    image = models.ImageField(upload_to='formations/', null=True, blank=True, verbose_name="Image de couverture")
    image_base64 = models.TextField(null=True, blank=True)
    tuteur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_tuteur', related_name='formations_dispensees',
        verbose_name="Tuteur référent"
    )
    prerequis = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        db_column='prerequis_id', related_name='formations_suivantes',
        verbose_name="Prérequis optionnel"
    )
    is_online = models.BooleanField(default=False, verbose_name="Format / En ligne")
    lien_api_room = models.CharField(max_length=255, null=True, blank=True, verbose_name="Lien Visioconférence")

    @property
    def date_debut(self):
        return self.date_formation

    @date_debut.setter
    def date_debut(self, value):
        self.date_formation = value

    @property
    def get_image_url(self):
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        if self.image_base64:
            return self.image_base64
        return None

    class Meta:
        db_table = 'formation'
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'

    def __str__(self):
        return f"{self.titre} ({self.niveau})"


class Inscription(models.Model):
    STATUT_CHOICES = [
        ('En attente', 'En attente'),
        ('En cours', 'En cours'),
        ('Terminée', 'Terminée'),
    ]

    id_inscription = models.AutoField(primary_key=True)
    candidat = models.ForeignKey(
        Candidat, on_delete=models.CASCADE, db_column='id_candidat', related_name='inscriptions'
    )
    formation = models.ForeignKey(
        Formation, on_delete=models.CASCADE, db_column='id_formation', related_name='inscriptions'
    )
    date_inscription = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='En attente')
    progression = models.IntegerField(default=0, help_text="Progression en % (0-100)")

    class Meta:
        db_table = 'inscription'
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'

    def save(self, *args, **kwargs):
        # Règle métier stricte (InscriptionController.php lignes 170-179):
        # progression == 0   <=> statut == 'En attente'
        # 0 < progression < 100 <=> statut == 'En cours'
        # progression == 100 <=> statut == 'Terminée'
        if self.progression is None:
            self.progression = 0
        self.progression = max(0, min(100, int(self.progression)))

        if self.progression >= 100:
            self.statut = 'Terminée'
        elif self.progression > 0:
            self.statut = 'En cours'
        else:
            self.statut = 'En attente'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Inscription de {self.candidat} à {self.formation.titre}"
