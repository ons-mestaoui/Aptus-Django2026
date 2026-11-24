from django.contrib import admin
from .models import OffreEmploi, Candidature

class CandidatureInline(admin.TabularInline):
    model = Candidature
    extra = 0
    readonly_fields = ('id_candidature',)

@admin.register(OffreEmploi)
class OffreEmploiAdmin(admin.ModelAdmin):
    list_display = ('id_offre', 'titre', 'entreprise', 'salaire', 'domaine', 'date_publication', 'date_expir')
    list_filter = ('domaine', 'date_publication')
    search_fields = ('titre', 'description', 'competences_requises', 'entreprise__raison_sociale')
    inlines = [CandidatureInline]

@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ('id_candidature', 'candidat', 'offre', 'statut', 'note')
    list_filter = ('statut',)
    search_fields = ('candidat__utilisateur__nom', 'candidat__utilisateur__prenom', 'offre__titre')
