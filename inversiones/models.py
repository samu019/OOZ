from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
import os
from random import randint
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django_cron import CronJobBase, Schedule
from uuid import uuid4
# -------------------------
# VIP y Solicitudes VIP
# -------------------------
class VIPLevel(models.Model):
    nombre = models.CharField(max_length=100)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    porcentaje_retorno = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tareas_diarias = models.IntegerField(default=0)
    ganancia_diaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duracion_dias = models.IntegerField(default=30)

    def __str__(self):
        return self.nombre

    def beneficio_mensual(self):
        return self.tareas_diarias * self.ganancia_diaria * 26

class UsuarioVIP(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nivel = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"VIP {self.user.username} - Nivel {self.nivel}"

# -------------------------
# USUARIO PERSONALIZADO
# -------------------------
class CustomUser(AbstractUser):
    email = models.CharField(max_length=100, blank=True, null=True)

    is_vip = models.BooleanField(default=False)
    vip_level = models.ForeignKey(
        'VIPLevel',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users'
    )
    vip_expiration = models.DateTimeField(null=True, blank=True)

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    wallet = models.CharField(max_length=100, blank=True, null=True)

    referido_por = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='referidos_set'
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def actualizar_estado_vip(self):
        if self.vip_expiration and timezone.now() > self.vip_expiration:
            self.is_vip = False
            self.vip_level = None
            self.save(update_fields=['is_vip', 'vip_level'])

    def __str__(self):
        return self.username

# -------------------------
# PERFIL DE USUARIO
# -------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    phone = models.CharField("Número de teléfono", max_length=20, blank=True, null=True)
    birthdate = models.DateField("Fecha de nacimiento", blank=True, null=True)
    address = models.TextField("Dirección", blank=True, null=True)
    bio = models.TextField("Información personal", blank=True, null=True)
    links = models.URLField("Enlace a soporte u otra URL", blank=True, null=True)

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)
    updated_at = models.DateTimeField("Última actualización", auto_now=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"

    def delete_photo(self):
        """Método para eliminar la foto de perfil"""
        if self.photo and os.path.isfile(self.photo.path):
            os.remove(self.photo.path)
            self.photo = None
            self.save()

    def save(self, *args, **kwargs):
        super(UserProfile, self).save(*args, **kwargs)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Señal para crear un perfil automáticamente cuando se crea un usuario."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Señal para guardar el perfil cada vez que se guarda el usuario."""
    instance.profile.save()

# -------------------------
# DEPÓSITOS CRYPTO
# -------------------------
def generar_direccion_billetera():
    """Genera una dirección única de billetera interna para un usuario."""
    return str(uuid4())

class CryptoDeposit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('failed', 'Fallido'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100, unique=True)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    amount_crypto = models.DecimalField(max_digits=20, decimal_places=8, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    txid = models.CharField(max_length=100, blank=True, null=True)
    captura_pago = models.ImageField(upload_to='capturas/', blank=True, null=True)
    retries = models.IntegerField(default=0)
    wallet = models.CharField(max_length=100, blank=True, null=True)  # Dirección de billetera interna

    def __str__(self):
        return f"Depósito {self.user.username} - {self.amount_usd} USD ({self.status})"

    def save(self, *args, **kwargs):
        """Genera una dirección de billetera interna si no se tiene."""
        if not self.wallet:
            self.wallet = generar_direccion_billetera()  # Genera una dirección interna
        super().save(*args, **kwargs)

# -------------------------
# RETIROS CRYPTO
# -------------------------
class CryptoWithdraw(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='crypto_withdraws')
    amount_usd = models.DecimalField(max_digits=18, decimal_places=8)  # Aumentamos la precisión de decimales
    wallet_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    def approve(self):
        self.status = 'approved'
        self.processed_at = timezone.now()
        self.save()

    def reject(self):
        self.status = 'rejected'
        self.processed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Retiro {self.user.username} - {self.amount_usd} USD ({self.status})"


# -------------------------
# TRANSACCIONES
# -------------------------
class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('ganancia', 'Ganancia'),
        ('retiro', 'Retiro'),
        ('deposito', 'Depósito'),
        ('bono', 'Bono'),
        ('tarea', 'Tarea'),
        ('inversion', 'Inversión'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transacciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.tipo in ['deposito', 'ganancia', 'bono', 'tarea']:
                self.user.balance += self.monto
            elif self.tipo in ['retiro', 'inversion']:
                self.user.balance -= self.monto
            self.user.save()
        super().save(*args, **kwargs)


# -------------------------
# TAREAS
# -------------------------
class Tarea(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

class TareaUsuario(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False)

    def __str__(self):
        return f"Tarea: {self.tarea.nombre} - Usuario: {self.usuario.username}"

class Referido(models.Model):
    referidor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referidos_directos')
    referido = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referencias_recibidas')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referido.username} fue referido por {self.referidor.username}"

# -------------------------
# INVERSIONES
# -------------------------
class Investment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inversiones')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_inversion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Inversión de {self.user.username} - ${self.amount}"

    @property
    def profitability(self):
        if self.amount and self.current_value:
            return float((self.current_value - self.amount) / self.amount * 100)
        return 0.0

# -------------------------
# HISTORIAL OOZ
# -------------------------
class HistorialOOZ(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='historial_ooz')
    tipo = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.tipo} - {self.monto} - {self.fecha}"

# -------------------------
# JUEGO DE INVERSION
# -------------------------
class JuegoInvestment(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tipo_juego = models.CharField(max_length=100)
    fecha_juego = models.DateTimeField(auto_now_add=True)
    investment = models.ForeignKey('Investment', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo_juego} - {self.fecha_juego}"

class SolicitudVIP(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='solicitudes_vip')
    vip = models.ForeignKey(VIPLevel, on_delete=models.PROTECT)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)

    def aprobar(self):
        self.estado = 'aprobado'
        self.fecha_aprobacion = timezone.now()
        self.save()

        usuario = self.user
        usuario.is_vip = True
        usuario.vip_level = self.vip
        usuario.vip_expiration = timezone.now() + timedelta(days=self.vip.duracion_dias)
        usuario.save()

    def rechazar(self):
        self.estado = 'rechazado'
        self.save()

    def __str__(self):
        return f"Solicitud VIP de {self.user.username} - {self.estado}"

# -------------------------
# DEPOSITOS Y RETIROS
# -------------------------
class Deposito(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('failed', 'Fallido'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Depósito {self.payment_id} - {self.amount_usd} USD"

    def restablecer_depositos(self):
        hoy = timezone.now()
        fecha_limite = hoy - timedelta(days=7)  # Depósitos mayores a 7 días
        self.objects.filter(status='pending', created_at__lte=fecha_limite).update(status='expirado')

class Retiro(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    wallet_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[('pending', 'Pendiente'), ('approved', 'Aprobado')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Retiro {self.amount_usd} USD - {self.wallet_address}"

class Task(models.Model):
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    recompensa = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class UserTask(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    completada = models.BooleanField(default=False)
    fecha_completada = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Task {self.task.title} for {self.user.username}"

class Referido(models.Model):
    usuario = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='referidos'
    )
    referidor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='referidos_invertidos',
        related_query_name='referidor'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} referido por {self.referidor.username}"

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

class RestaurarDepositosCronJob(CronJobBase):
    schedule = Schedule(run_every_mins=10080)  # Ejecutar cada semana (10080 minutos)
    code = 'inversiones.restaurar_depositos'

    def do(self):
        Deposito.restablecer_depositos()

class MiCronJob(CronJobBase):
    schedule = Schedule(run_every_mins=60)  # Esto ejecuta el cronjob cada hora
    code = 'miapp.micronjob'  # Un identificador único

    def do(self):
        # Lógica que se ejecutará
        print("CronJob ejecutado con éxito")

User = get_user_model()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet_account')
    balance = models.DecimalField(max_digits=18, decimal_places=8, default=0.0)
    address = models.CharField(max_length=255, unique=True, default=uuid4)

    def __str__(self):
        return f"Billetera de {self.user.username}"

    def deposit(self, amount):
        """Método para agregar saldo a la billetera."""
        if amount <= 0:
            raise ValueError("El monto a depositar debe ser mayor que 0.")
        self.balance += amount
        self.save()

    def withdraw(self, amount):
        """Método para retirar saldo de la billetera."""
        if amount <= 0:
            raise ValueError("El monto a retirar debe ser mayor que 0.")
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False  # Si no hay suficiente saldo, retornamos False


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """Crear billetera interna cuando se crea un nuevo usuario."""
    if created:
        Wallet.objects.create(user=instance)
