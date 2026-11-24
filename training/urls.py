from django.urls import path
from . import views

app_name = 'training'

urlpatterns = [
    path('', views.formation_list, name='formation_list'),
    path('mes-formations/', views.formation_my, name='formation_my'),
    path('creer/', views.formation_create, name='formation_create'),
    path('<int:pk>/', views.formation_detail, name='formation_detail'),
    path('<int:pk>/cours/', views.formation_viewer, name='formation_viewer'),
    path('<int:pk>/sinscrire/', views.formation_sinscrire, name='formation_sinscrire'),
    path('inscriptions/<int:pk>/desinscrire/', views.formation_desinscrire, name='formation_desinscrire'),
    path('<int:pk>/modifier/', views.formation_update, name='formation_update'),
    path('<int:pk>/supprimer/', views.formation_delete, name='formation_delete'),
]
