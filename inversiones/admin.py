from django.contrib import admin
from django.db.models import Sum
from django.template.response import TemplateResponse
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Task, UserTask, Investment, VIPLevel, SolicitudVIP, CryptoDeposit, CryptoWithdraw, Deposito
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import admin
from .models import Wallet  # Importa el modelo Wallet
# ============================
#   Admin personalizado
# ============================
class MyAdminSite(admin.AdminSite):
    site_header = 'Plataforma OOZ - Panel Admin'
    site_title = 'Panel de Administración OOZ'
    index_title = 'Resumen de la Plataforma'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_view(self.dashboard_view), name='index'),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        total_usuarios = CustomUser.objects.count()
        saldo_total = CustomUser.objects.aggregate(total=Sum('balance'))['total'] or 0
        depositos = CryptoDeposit.objects.all()
        inversiones_total = Investment.objects.aggregate(total=Sum('amount'))['total'] or 0
        inversiones_activas = Investment.objects.filter(activo=True).count()

        context = dict(
            self.each_context(request),
            total_usuarios=total_usuarios,
            saldo_total=saldo_total,
            depositos_pendientes=depositos.filter(status='pending').count(),
            depositos_confirmados=depositos.filter(status='confirmed').count(),
            ultimos_depositos=depositos.order_by('-created_at')[:5],
            total_inversiones=inversiones_total,
            inversiones_activas=inversiones_activas,
        )
        return TemplateResponse(request, "admin/dashboard.html", context)


# ============================
#   CustomUser
# ============================
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'is_vip', 'balance', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('is_vip', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}), 
        (_('Información personal'), {'fields': (
            'first_name', 'last_name', 'email', 'balance', 'wallet',
            'referido_por', 'is_vip', 'vip_expiration'
        )}),
        (_('Permisos'), {'fields': (
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
        )}),
        (_('Fechas importantes'), {'fields': ('last_login', 'date_joined')}), 
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


# ============================
#   VIP Levels
# ============================
class VIPLevelAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'costo', 'porcentaje_retorno',
        'tareas_diarias', 'ganancia_diaria', 'duracion_dias', 'beneficio_mensual'
    )
    search_fields = ('nombre',)

    def beneficio_mensual(self, obj):
        return f"{obj.ganancia_diaria * obj.tareas_diarias * 26:.2f} USD"
    beneficio_mensual.short_description = "Beneficio mensual"


# ============================
#   UserTask
# ============================
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'completada', 'fecha_completada')
    list_filter = ('completada',)
    search_fields = ('user__username', 'task__titulo')


# ============================
#   Investment
# ============================
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'fecha_inversion', 'activo', 'current_value')
    list_filter = ('activo', 'fecha_inversion')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('fecha_inversion',)


# ============================
#   SolicitudVIP
# ============================
@admin.register(SolicitudVIP)
class SolicitudVIPAdmin(admin.ModelAdmin):
    list_display = ('user', 'vip', 'estado', 'fecha_solicitud', 'fecha_aprobacion')
    list_filter = ('estado',)
    actions = ['aprobar_solicitudes', 'rechazar_solicitudes']

    def aprobar_solicitudes(self, request, queryset):
        for solicitud in queryset.filter(estado='pendiente'):
            solicitud.aprobar()
        self.message_user(request, "Solicitudes aprobadas con éxito.")
    aprobar_solicitudes.short_description = "Aprobar solicitudes seleccionadas"

    def rechazar_solicitudes(self, request, queryset):
        for solicitud in queryset.filter(estado='pendiente'):
            solicitud.rechazar()
        self.message_user(request, "Solicitudes rechazadas.")
    rechazar_solicitudes.short_description = "Rechazar solicitudes seleccionadas"


# ============================
#   CryptoDeposit Admin
# ============================
@admin.register(CryptoDeposit)
class CryptoDepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_id', 'amount_usd', 'status', 'created_at', 'confirmed_at', 'txid', 'captura_pago', 'acciones')
    list_filter = ('status',)
    search_fields = ('user__username', 'payment_id', 'txid')
    readonly_fields = ('created_at', 'confirmed_at')

    actions = ['aprobar_depositos', 'rechazar_depositos', 'confirmar_deposito', 'fallar_deposito', 'eliminar_depositos', 'recuperar_depositos']

    def aprobar_depositos(self, request, queryset):
        updated = queryset.update(status='confirmed', confirmed_at=timezone.now())
        self.message_user(request, f"{updated} depósito(s) aprobado(s).")
    aprobar_depositos.short_description = "Aprobar depósitos seleccionados"

    def rechazar_depositos(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f"{updated} depósito(s) rechazado(s).")
    rechazar_depositos.short_description = "Rechazar depósitos seleccionados"

    def confirmar_deposito(self, request, queryset):
        # Confirmar depósitos pendientes
        updated = queryset.filter(status='pending').update(status='confirmed', confirmed_at=timezone.now())
        self.message_user(request, f"{updated} depósito(s) confirmado(s).")
    confirmar_deposito.short_description = "Confirmar depósitos pendientes"

    def fallar_deposito(self, request, queryset):
        # Marcar depósitos pendientes como fallidos
        updated = queryset.filter(status='pending').update(status='failed')
        self.message_user(request, f"{updated} depósito(s) fallido(s).")
    fallar_deposito.short_description = "Marcar depósitos como fallidos"

    def eliminar_depositos(self, request, queryset):
        # Marcar depósitos como eliminados
        updated = queryset.update(status='deleted')
        self.message_user(request, f"{updated} depósito(s) marcado(s) como eliminados.")
    eliminar_depositos.short_description = "Eliminar depósitos seleccionados"

    def recuperar_depositos(self, request, queryset):
        # Recuperar depósitos eliminados
        updated = queryset.filter(status='deleted').update(status='pending')
        self.message_user(request, f"{updated} depósito(s) recuperado(s).")
    recuperar_depositos.short_description = "Recuperar depósitos eliminados"

    def txid(self, obj):
        # Mostrar TXID
        return obj.txid if obj.txid else "No disponible"
    txid.short_description = "TXID"

    def captura_pago(self, obj):
        # Mostrar la captura de pago si existe
        if obj.captura_pago:
            return f'<a href="{obj.captura_pago.url}" target="_blank">Ver captura</a>'
        return "No disponible"
    captura_pago.allow_tags = True
    captura_pago.short_description = "Captura de Pago"

    def acciones(self, obj):
       return format_html(
        '<a class="button" href="{}">Confirmar</a>&nbsp;|&nbsp;'
        '<a class="button" href="{}">Rechazar</a>',
        self.confirmar_deposito_url(obj),
        self.fallar_deposito_url(obj),
    )

    acciones.short_description = 'Acciones'

    def confirmar_deposito_url(self, obj):
        # URL para confirmar el depósito
        return f"/admin/{obj._meta.app_label}/{obj._meta.model_name}/{obj.pk}/confirmar/"

    def fallar_deposito_url(self, obj):
        # URL para fallar el depósito
        return f"/admin/{obj._meta.app_label}/{obj._meta.model_name}/{obj.pk}/fallar/"

# ============================
#   Deposito Admin
# ============================
@admin.register(Deposito)
class DepositoAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_id', 'amount_usd', 'status', 'created_at', 'acciones')
    list_filter = ('status',)
    search_fields = ('user__username', 'payment_id')
    readonly_fields = ('created_at',)

    actions = ['aprobar_depositos', 'rechazar_depositos', 'confirmar_deposito', 'fallar_deposito', 'eliminar_depositos', 'recuperar_depositos']

    def aprobar_depositos(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} depósito(s) aprobado(s).")
    aprobar_depositos.short_description = "Aprobar depósitos seleccionados"

    def rechazar_depositos(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f"{updated} depósito(s) rechazado(s).")
    rechazar_depositos.short_description = "Rechazar depósitos seleccionados"

    def confirmar_deposito(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f"{updated} depósito(s) confirmado(s).")
    confirmar_deposito.short_description = "Confirmar depósitos pendientes"

    def fallar_deposito(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='failed')
        self.message_user(request, f"{updated} depósito(s) fallido(s).")
    fallar_deposito.short_description = "Marcar depósitos como fallidos"

    def eliminar_depositos(self, request, queryset):
        updated = queryset.update(status='deleted')
        self.message_user(request, f"{updated} depósito(s) marcado(s) como eliminados.")
    eliminar_depositos.short_description = "Eliminar depósitos seleccionados"

    def recuperar_depositos(self, request, queryset):
        updated = queryset.filter(status='deleted').update(status='pending')
        self.message_user(request, f"{updated} depósito(s) recuperado(s).")
    recuperar_depositos.short_description = "Recuperar depósitos eliminados"

    def acciones(self, obj):
        return format_html(
            '<a class="button" href="{}">Confirmar</a>&nbsp;|&nbsp;'
            '<a class="button" href="{}">Rechazar</a>',
            self.confirmar_deposito_url(obj),
            self.fallar_deposito_url(obj),
        )
    acciones.short_description = 'Acciones'

    def confirmar_deposito_url(self, obj):
        return f"/admin/{obj._meta.app_label}/{obj._meta.model_name}/{obj.pk}/confirmar/"

    def fallar_deposito_url(self, obj):
        return f"/admin/{obj._meta.app_label}/{obj._meta.model_name}/{obj.pk}/fallar/"

# ============================
#   CryptoWithdraw Admin
# ============================
@admin.register(CryptoWithdraw)
class CryptoWithdrawAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_usd", "wallet_address", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "wallet_address")
    actions = ['aprobar', 'rechazar']

    def aprobar(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} retiro(s) aprobado(s).")
    aprobar.short_description = "Aprobar retiros seleccionados"

    def rechazar(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} retiro(s) rechazado(s).")
    rechazar.short_description = "Rechazar retiros seleccionados"

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'address')
    search_fields = ('user__username',)


# ============================
#   Registro en admin personalizado
# ============================
my_admin_site = MyAdminSite(name='myadmin')

# Registros
my_admin_site.register(CustomUser, CustomUserAdmin)
my_admin_site.register(Task)
my_admin_site.register(UserTask, UserTaskAdmin)
my_admin_site.register(Investment, InvestmentAdmin)
my_admin_site.register(VIPLevel, VIPLevelAdmin)
my_admin_site.register(SolicitudVIP, SolicitudVIPAdmin)
my_admin_site.register(CryptoDeposit, CryptoDepositAdmin)
my_admin_site.register(Deposito, DepositoAdmin)
my_admin_site.register(CryptoWithdraw, CryptoWithdrawAdmin)
