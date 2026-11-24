from django.db import models
from accounts.models import Administrateur


class RapportMarche(models.Model):
    id_rapport_marche = models.AutoField(primary_key=True)
    admin = models.ForeignKey(
        Administrateur, on_delete=models.CASCADE, db_column='id_admin', null=True, blank=True, related_name='rapports'
    )
    titre = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    contenu_detaille = models.TextField(null=True, blank=True)
    image_couverture = models.TextField(null=True, blank=True)
    date_publication = models.DateField(null=True, blank=True)
    region = models.CharField(max_length=255, null=True, blank=True)
    secteur_principal = models.CharField(max_length=255, null=True, blank=True)
    salaire_moyen_global = models.FloatField(null=True, blank=True)
    salaire_min_global = models.FloatField(null=True, blank=True)
    salaire_max_global = models.FloatField(null=True, blank=True)
    tendance_generale = models.CharField(max_length=255, null=True, blank=True)
    niveau_demande_global = models.IntegerField(null=True, blank=True)
    nombre_donnees = models.IntegerField(null=True, blank=True)
    auteur = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'rapport_marche'
        verbose_name = 'Rapport Marché'
        verbose_name_plural = 'Rapports Marché'

    def __str__(self):
        return f"{self.titre} ({self.region or 'National'})"


class ReferenceRapport(models.Model):
    id_reference = models.AutoField(primary_key=True)
    rapport_marche = models.ForeignKey(
        RapportMarche, on_delete=models.CASCADE, related_name='references'
    )
    titre_source = models.CharField(max_length=255)
    url_source = models.URLField(max_length=500, null=True, blank=True)
    note_source = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'reference_rapport'
        verbose_name = 'Référence Rapport'
        verbose_name_plural = 'Références Rapports'

    def __str__(self):
        return self.titre_source


class DonneeMarche(models.Model):
    id_donnee = models.AutoField(primary_key=True)
    rapport_marche = models.ForeignKey(
        RapportMarche, on_delete=models.CASCADE, db_column='id_rapport_marche', related_name='donnees'
    )
    domaine = models.CharField(max_length=255, null=True, blank=True)
    competence = models.CharField(max_length=255, null=True, blank=True)
    salaire_min = models.FloatField(null=True, blank=True)
    salaire_max = models.FloatField(null=True, blank=True)
    salaire_moyen = models.FloatField(null=True, blank=True)
    demande = models.IntegerField(null=True, blank=True)
    date_collecte = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'donnee_marche'
        verbose_name = 'Donnée Marché'
        verbose_name_plural = 'Données Marché'

    def __str__(self):
        return f"{self.competence} ({self.domaine}) - Demande: {self.demande}"
