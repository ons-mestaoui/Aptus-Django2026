from django.contrib import admin
from .models import RapportMarche, ReferenceRapport


class ReferenceRapportInline(admin.TabularInline):
    model = ReferenceRapport
    extra = 1


@admin.register(RapportMarche)
class RapportMarcheAdmin(admin.ModelAdmin):
    list_display = ('id_rapport_marche', 'titre', 'region', 'secteur_principal', 'salaire_moyen_global', 'date_publication')
    list_filter = ('region', 'secteur_principal')
    search_fields = ('titre', 'description', 'contenu_detaille', 'region', 'secteur_principal')
    inlines = [ReferenceRapportInline]


@admin.register(ReferenceRapport)
class ReferenceRapportAdmin(admin.ModelAdmin):
    list_display = ('id_reference', 'titre_source', 'url_source', 'rapport_marche')
    search_fields = ('titre_source', 'note_source', 'url_source')
