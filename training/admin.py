from django.contrib import admin
from .models import Formation, Inscription

class InscriptionInline(admin.TabularInline):
    model = Inscription
    extra = 0

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('id_formation', 'titre', 'domaine', 'niveau', 'tuteur', 'is_online', 'date_formation')
    list_filter = ('niveau', 'is_online', 'domaine')
    search_fields = ('titre', 'description', 'domaine')
    inlines = [InscriptionInline]

@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('id_inscription', 'candidat', 'formation', 'statut', 'progression', 'date_inscription')
    list_filter = ('statut',)
    search_fields = ('candidat__utilisateur__nom', 'candidat__utilisateur__prenom', 'formation__titre')
