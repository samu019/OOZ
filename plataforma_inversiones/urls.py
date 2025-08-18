# urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from inversiones import views
from inversiones.admin import my_admin_site
from inversiones.views import invertir_ajax
from inversiones.views import invitar_view
from django.urls import path
from inversiones.views import confirmar_deposito, fallar_deposito



urlpatterns = [
    # --- Inicio y autenticación ---
    path('', views.home_view, name='home'),
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- Dashboard ---
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('perfil/cambiar-contrasena/', views.cambiar_contraseña, name='cambiar_contrasena'),

    # --- Perfil del usuario ---
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/ajax-actualizar/', views.ajax_actualizar_perfil, name='ajax_actualizar_perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/cambiar-contrasena/', views.cambiar_contraseña, name='cambiar_contrasena'),
    path('perfil/actualizar_foto/', views.perfil_actualizar_foto, name='perfil_actualizar_foto'),
    path('perfil/eliminar_foto/', views.perfil_eliminar_foto, name='perfil_eliminar_foto'),
    # urls.py
    path('perfil/actualizar-campo/', views.actualizar_campo_perfil, name='perfil_update_field'),
    path('invitar/<int:user_id>/', invitar_view, name='invitar'),
    path('notificaciones/', views.obtener_notificaciones, name='notificaciones'),

    # --- Depósitos y Retiros ---
    # Actualizamos las rutas de depósito para usar las vistas internas
    path('depositar/', views.crear_deposito, name='crear_deposito'),  # Ahora usa la vista de crear depósito
    path('deposito/inicio/', views.deposito_inicio, name='deposito_inicio'),
    path('deposito/direccion/', views.deposito_direccion_pago, name='deposito_direccion'),
    path('deposito/captura/', views.deposito_captura, name='deposito_captura'),
    path('deposito/webhook/', views.webhook_interno, name='deposito_webhook'),  # Ruta para el webhook interno
    path('depositos/', views.depositos_view, name='depositos'),
    path('deposito/direccion/<int:deposito_id>/', views.direccion_pago, name='direccion_pago'),
    path('deposito/estado/<int:deposito_id>/', views.estado_deposito, name='estado_deposito'),
    path('deposito/subir_pago/<int:deposito_id>/', views.subir_captura_pago, name='subir_pago'),
   

    # --- Rutas para confirmar y fallar depósitos (fuera del admin) ---
    path('admin/depositos/<int:id>/confirmar/', confirmar_deposito, name='confirmar_deposito'),
    path('admin/depositos/<int:id>/fallar/', fallar_deposito, name='fallar_deposito'),
    
    # Rutas para finalizar y obtener información del depósito
    path('finalizar-deposito/<int:deposito_id>/', views.finalizar_deposito, name='finalizar_deposito'),
    path('informacion-deposito/<int:deposito_id>/', views.informacion_deposito, name='informacion_deposito'),

    # Retiros
    path('retiro/solicitar/', views.solicitar_retiro, name='solicitar_retiro'),
    path('retiros/aprobados/', views.retiros_aprobados_view, name='retiros_aprobados'),
    path('retiros-status/', views.retiros_status_view, name='retiros_status'),
    path('retirar/', views.withdraw_view, name='retirar'),

    # --- VIP ---
    path('vip/', views.lista_vip_view, name='lista_vip'),
    path('vip/desbloquear/<int:vip_id>/', views.desbloquear_vip, name='desbloquear_vip'),
    path('vip/solicitar/<int:vip_id>/', views.solicitar_vip, name='solicitar_vip'),
    path('comprar-vip/', views.comprar_vip_view, name='comprar_vip'),
    path('vip-levels/', views.vip_levels_view, name='vip_levels'),

    # --- Tareas ---
    path('tareas/diarias/', views.tareas_diarias_view, name='tareas_diarias'),
    path('tareas/realizar/<int:tarea_id>/', views.realizar_tarea, name='realizar_tarea'),
    path('tareas/completar/<int:task_id>/', views.completar_tarea, name='completar_tarea'),
    path('tareas/historial/', views.historial_tareas_view, name='historial_tareas'),

    # --- Juegos ---
    path('invertir/', views.jugar_para_ganar, name='invertir'),
    path('juegos/', views.jugar_para_ganar, name='juegos'),
    path('jugar/<str:tipo_juego>/', views.jugar_juego, name='jugar_juego'),
    path('jugar/iniciar/<int:juego_id>/', views.iniciar_juego, name='iniciar_juego'),
    path('juego/<int:juego_id>/jugar/', views.jugar_inversion, name='jugar_inversion'),
    path('resultado/<int:juego_id>/', views.resultado_juego, name='resultado_juego'),

    # --- Estadísticas y Finanzas ---
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('finanzas/', views.finanzas_view, name='finanzas'),
    path('descargar-historial/', views.descargar_historial, name='descargar_historial'),
    path('configuracion/', views.configuracion_view, name='configuracion'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('cambiar-contraseña/', views.cambiar_contraseña, name='cambiar_contraseña'),
    # --- Referidos y Soporte ---
    path('referidos/', views.referidos_view, name='mis_referidos'),
    path('soporte/', views.soporte_view, name='soporte'),
    path('depositar/', views.crear_deposito, name='depositar'),
    
    # --- API ---
    path('api/invertir/', invertir_ajax, name='invertir_ajax'),

    # --- Admin personalizado ---
    path('admin/', my_admin_site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
