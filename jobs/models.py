from django.db import models
from accounts.models import Entreprise, Candidat

class OffreEmploi(models.Model):
    id_offre = models.AutoField(primary_key=True)
    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, db_column='id_entreprise', related_name='offres'
    )
    titre = models.CharField(max_length=255)
    description = models.TextField()
    competences_requises = models.TextField(null=True, blank=True)
    salaire = models.FloatField(null=True, blank=True)
    date_expir = models.DateField(null=True, blank=True)
    domaine = models.CharField(max_length=255, null=True, blank=True)
    experience_requise = models.CharField(max_length=255, null=True, blank=True)
    date_publication = models.DateField(auto_now_add=True)
    question = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = 'offreemploi'
        verbose_name = "Offre d'emploi"
        verbose_name_plural = "Offres d'emploi"

    def __str__(self):
        return f"{self.titre} ({self.entreprise.raison_sociale or self.entreprise.utilisateur.nom})"


class Candidature(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('shortliste', 'Shortlisté'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
    ]

    id_candidature = models.AutoField(primary_key=True)
    candidat = models.ForeignKey(
        Candidat, on_delete=models.CASCADE, db_column='id_candidat', related_name='candidatures'
    )
    offre = models.ForeignKey(
        OffreEmploi, on_delete=models.CASCADE, db_column='id_offre', related_name='candidatures'
    )
    reponses_ques = models.TextField(null=True, blank=True, verbose_name="Réponses aux questions")
    cv_cand = models.FileField(
        upload_to='candidatures_cvs/',
        db_column='cv__cand',
        null=False,
        blank=False,
        default='candidatures_cvs/default.pdf',
        verbose_name="CV joint"
    )
    note = models.FloatField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    class Meta:
        db_table = 'candidatures'
        unique_together = (('candidat', 'offre'),)
        verbose_name = 'Candidature'
        verbose_name_plural = 'Candidatures'

    def __str__(self):
        return f"Candidature #{self.id_candidature} - {self.candidat} pour {self.offre.titre}"
