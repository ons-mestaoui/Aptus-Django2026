from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.utilisateur_list, name='utilisateur_list'),
    path('parametres/', views.account_settings, name='settings'),
    path('profil/', views.profile_view, name='profile'),
    path('creer/', views.utilisateur_create, name='utilisateur_create'),
    path('<int:pk>/', views.utilisateur_detail, name='utilisateur_detail'),
    path('<int:pk>/modifier/', views.utilisateur_update, name='utilisateur_update'),
    path('<int:pk>/supprimer/', views.utilisateur_delete, name='utilisateur_delete'),
]
