from django.urls import path
from . import views

app_name = 'cv_studio'

urlpatterns = [
    path('', views.cv_list, name='cv_list'),
    path('templates/', views.template_list, name='template_list'),
    path('creer/', views.cv_create, name='cv_create'),
    path('<int:pk>/', views.cv_detail, name='cv_detail'),
    path('<int:pk>/imprimer/', views.cv_print, name='cv_print'),
    path('<int:pk>/modifier/', views.cv_update, name='cv_update'),
    path('<int:pk>/supprimer/', views.cv_delete, name='cv_delete'),
]
