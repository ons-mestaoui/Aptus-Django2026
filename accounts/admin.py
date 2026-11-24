from django.contrib import admin
from .models import Utilisateur, Administrateur, Candidat, Entreprise, Profil

@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('id_utilisateur', 'prenom', 'nom', 'email', 'role', 'telephone')
    list_filter = ('role',)
    search_fields = ('nom', 'prenom', 'email', 'telephone')
    ordering = ('id_utilisateur',)

@admin.register(Administrateur)
class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'niveau')
    search_fields = ('utilisateur__nom', 'utilisateur__prenom', 'niveau')

@admin.register(Candidat)
class CandidatAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'niveau_etudes', 'niveau')
    search_fields = ('utilisateur__nom', 'utilisateur__prenom', 'competences')
    list_filter = ('niveau_etudes', 'niveau')

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ('raison_sociale', 'utilisateur', 'secteur', 'siret')
    search_fields = ('raison_sociale', 'siret', 'secteur', 'utilisateur__nom')
    list_filter = ('secteur',)

@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('id_profil', 'utilisateur', 'ville', 'pays', 'date_naissance')
    search_fields = ('utilisateur__nom', 'utilisateur__prenom', 'ville', 'pays')
