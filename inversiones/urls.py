from django.urls import path
from inversiones import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('invertir/', views.crear_inversion_view, name='crear_inversion'),  # Nombre para link
   
]
