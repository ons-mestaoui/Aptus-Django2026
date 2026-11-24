from django.urls import path
from . import views

app_name = 'market'

urlpatterns = [
    path('', views.rapport_list, name='rapport_list'),
    path('creer/', views.rapport_create, name='rapport_create'),
    path('<int:pk>/', views.rapport_detail, name='rapport_detail'),
    path('<int:pk>/modifier/', views.rapport_update, name='rapport_update'),
    path('<int:pk>/supprimer/', views.rapport_delete, name='rapport_delete'),
]
