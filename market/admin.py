from django.contrib import admin
from .models import RapportMarche, DonneeMarche

class DonneeMarcheInline(admin.TabularInline):
    model = DonneeMarche
    extra = 1

@admin.register(RapportMarche)
class RapportMarcheAdmin(admin.ModelAdmin):
    list_display = ('id_rapport_marche', 'titre', 'region', 'secteur_principal', 'salaire_moyen_global', 'date_publication')
    list_filter = ('region', 'secteur_principal')
    search_fields = ('titre', 'description', 'region', 'secteur_principal')
    inlines = [DonneeMarcheInline]

@admin.register(DonneeMarche)
class DonneeMarcheAdmin(admin.ModelAdmin):
    list_display = ('id_donnee', 'competence', 'domaine', 'salaire_moyen', 'demande', 'rapport_marche')
    list_filter = ('domaine',)
    search_fields = ('competence', 'domaine')
