from django.db import models
from accounts.models import Candidat

class Template(models.Model):
    id_template = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    url_miniature = models.TextField(null=True, blank=True, db_column='urlMiniature')
    structure_html = models.TextField(null=True, blank=True, db_column='structureHtml')
    est_premium = models.BooleanField(default=False, db_column='estPremium')
    date_creation = models.DateTimeField(auto_now_add=True, db_column='dateCreation')

    class Meta:
        db_table = 'template'
        verbose_name = 'Modèle de CV'
        verbose_name_plural = 'Modèles de CV'

    def __str__(self):
        return self.nom


class CV(models.Model):
    id_cv = models.AutoField(primary_key=True)
    candidat = models.ForeignKey(
        Candidat, on_delete=models.CASCADE, db_column='id_candidat', related_name='cvs'
    )
    template = models.ForeignKey(
        Template, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_template', related_name='cvs'
    )
    nom_document = models.CharField(max_length=255, db_column='nomDocument')
    nom_complet = models.CharField(max_length=255, db_column='nomComplet')
    titre_poste = models.CharField(max_length=255, null=True, blank=True, db_column='titrePoste')
    resume = models.TextField(null=True, blank=True)
    info_contact = models.TextField(null=True, blank=True, db_column='infoContact')
    experience = models.TextField(null=True, blank=True)
    formation = models.TextField(null=True, blank=True)
    competences = models.TextField(null=True, blank=True)
    langues = models.TextField(null=True, blank=True)
    url_photo = models.TextField(null=True, blank=True, db_column='urlPhoto')
    couleur_theme = models.CharField(max_length=50, null=True, blank=True, db_column='couleurTheme')
    statut = models.CharField(max_length=50, null=True, blank=True, default='Actif')
    date_creation = models.DateTimeField(auto_now_add=True, db_column='dateCreation')
    date_mise_a_jour = models.DateTimeField(auto_now=True, db_column='dateMiseAJour')
    ai_analysis = models.TextField(null=True, blank=True)
    is_tailored = models.BooleanField(default=False)
    target_job_url = models.TextField(null=True, blank=True)
    tailoring_report = models.TextField(null=True, blank=True)
    job_url = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        db_table = 'cv'
        verbose_name = 'Curriculum Vitae'
        verbose_name_plural = 'Curriculums Vitae'

    def __str__(self):
        return f"{self.nom_document} ({self.nom_complet})"


class RapportIA(models.Model):
    id_rapport_ia = models.AutoField(primary_key=True)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, db_column='id_cv', related_name='rapports_ia')
    score_global = models.IntegerField(null=True, blank=True, db_column='scoreGlobal')
    points_forts = models.TextField(null=True, blank=True, db_column='pointsForts')
    points_faibles = models.TextField(null=True, blank=True, db_column='pointsFaibles')
    sections_manquantes = models.TextField(null=True, blank=True, db_column='sectionsManquantes')
    suggestions = models.TextField(null=True, blank=True)
    date_analyse = models.DateTimeField(auto_now_add=True, db_column='dateAnalyse')

    class Meta:
        db_table = 'rapport_ia'
        verbose_name = 'Rapport IA'
        verbose_name_plural = 'Rapports IA'

    def __str__(self):
        return f"Rapport IA - {self.cv.nom_document} (Score: {self.score_global}/100)"


class GuideRecrutement(models.Model):
    id_guide = models.AutoField(primary_key=True)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, db_column='id_cv', related_name='guides')
    candidat = models.ForeignKey(
        Candidat, on_delete=models.CASCADE, db_column='id_candidat', null=True, blank=True, related_name='guides'
    )
    titre_poste = models.CharField(max_length=255, null=True, blank=True)
    contenu_json = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'guide_recrutement'
        verbose_name = 'Guide de Recrutement'
        verbose_name_plural = 'Guides de Recrutement'

    def __str__(self):
        return f"Guide: {self.titre_poste or 'Général'} ({self.cv.nom_document})"
