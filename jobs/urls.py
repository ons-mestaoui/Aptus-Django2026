from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Offres (Catalogue & Détails Candidat)
    path('', views.offre_list, name='offre_list'),
    path('creer/', views.offre_create, name='offre_create'),
    path('<int:pk>/', views.offre_detail, name='offre_detail'),
    path('<int:pk>/postuler/', views.offre_postuler, name='offre_postuler'),
    path('<int:pk>/modifier/', views.offre_update, name='offre_update'),
    path('<int:pk>/supprimer/', views.offre_delete, name='offre_delete'),
    
    # Espace Entreprise (Portail RH authentique de hr_posts.php et hr_candidatures.php)
    path('entreprise/postes/', views.entreprise_posts, name='entreprise_posts'),
    path('entreprise/candidatures/', views.entreprise_candidatures, name='entreprise_candidatures'),

    # Espace Candidat : Candidatures
    path('candidatures/', views.candidature_list, name='candidature_list'),
    path('candidatures/creer/', views.candidature_create, name='candidature_create'),
    path('candidatures/<int:pk>/annuler/', views.candidature_annuler, name='candidature_annuler'),
    path('candidatures/<int:pk>/modifier/', views.candidature_update, name='candidature_update'),
    path('candidatures/<int:pk>/supprimer/', views.candidature_delete, name='candidature_delete'),
]
