from django.contrib import admin
from .models import Template, CV, RapportIA, GuideRecrutement

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('id_template', 'nom', 'est_premium', 'date_creation')
    list_filter = ('est_premium',)
    search_fields = ('nom', 'description')

@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ('id_cv', 'nom_document', 'nom_complet', 'titre_poste', 'candidat', 'statut', 'date_mise_a_jour')
    list_filter = ('statut', 'is_tailored')
    search_fields = ('nom_document', 'nom_complet', 'titre_poste', 'competences')

@admin.register(RapportIA)
class RapportIAAdmin(admin.ModelAdmin):
    list_display = ('id_rapport_ia', 'cv', 'score_global', 'date_analyse')
    list_filter = ('date_analyse',)
    search_fields = ('cv__nom_document', 'cv__nom_complet', 'suggestions')

@admin.register(GuideRecrutement)
class GuideRecrutementAdmin(admin.ModelAdmin):
    list_display = ('id_guide', 'titre_poste', 'cv', 'candidat', 'date_creation')
    search_fields = ('titre_poste', 'cv__nom_document')
