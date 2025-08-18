# ==========================
# Librerías estándar
# ==========================
import csv
import json
import requests
from .models import CustomUser  # Asegúrate de que el modelo esté importado correctamente
from .models import Referido 
from .models import Transaccion
from io import StringIO
from .models import UsuarioVIP  
from random import randint
from .models import Tarea
from .models import Wallet, Retiro  # Importamos Wallet y Retiro desde models.py
import subprocess
import random
import hmac
from .models import CryptoDeposit, CustomUser, generar_direccion_billetera 
import hashlib
from .models import Notification
from .models import CryptoDeposit, CryptoWithdraw
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from decimal import Decimal
from django.utils.crypto import get_random_string
from django.http import JsonResponse, HttpResponse
from itertools import chain
from django.db.models import Sum, Count
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate, login, logout, get_user_model, update_session_auth_hash
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
# views.py
from .models import TareaUsuario


# ==========================
# FORMULARIOS
# ==========================
from .forms import (
    RegistroForm,
    DepositoForm,  # Corregido para evitar duplicación
    RetiroForm,
    UserProfileForm,
    CustomPasswordChangeForm,
    CryptoDepositForm,
    CryptoWithdrawForm
)

# ==========================
# MODELOS
# ==========================
from .models import (
    Investment,
    JuegoInvestment,
    Tarea,
    TareaUsuario,
    Task,
    UserTask,
    VIPLevel,
    SolicitudVIP,
    CustomUser,
    UserProfile,
    Transaccion,
    Retiro,
    Deposito,
    CryptoDeposit,
    CryptoWithdraw
)

User = get_user_model()

# ==========================
# CONSTANTES
# ==========================
MAX_TAREAS_DIARIAS = 5
MAX_JUEGOS_DIARIOS = 3
JUEGO_COSTO = 10



# ==========================
# REGISTRO DE USUARIO
# ==========================
def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, "Registro exitoso. Ya puedes iniciar sesión.")
            return redirect('login')
        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

# ==========================
# LOGIN
# ==========================
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
        messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def home_view(request):
    return render(request, 'home.html')
# ==========================
# LOGOUT
# ==========================
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    user = request.user
    hoy = timezone.now().date()

    # Obtener el depósito pendiente (si existe)
    deposito_pendiente = CryptoDeposit.objects.filter(user=user, status='pending').first()

    # Finalizar investment y calcular ganancias
    if request.method == "POST":
        investment_id = request.POST.get("investment_id")
        if investment_id:
            with transaction.atomic():
                # Buscar la inversión activa
                investment = get_object_or_404(Investment, id=investment_id, user=user, activo=True)

                # Calcular la ganancia (Ejemplo: 20%)
                ganancia = investment.amount * Decimal('1.20')  # 20% de ganancia
                user.balance += ganancia  # Aumentamos el balance del usuario
                user.save()  # Guardamos el balance actualizado

                # Marcar la inversión como finalizada
                investment.activo = False
                investment.save()

                # Crear una transacción de ganancia para el usuario
                Transaccion.objects.create(
                    user=user,
                    tipo='ganancia',
                    monto=ganancia,
                    descripcion=f'Ganancia de investment {investment.id}'
                )

                messages.success(request, f"Investment finalizado. Ganaste ${ganancia:.2f}")
                return redirect('dashboard')

    # Obtener los referidos del usuario
    referidos = Referido.objects.filter(referidor=user)

    # Obtener inversiones activas y finalizadas
    inversiones_activas = Investment.objects.filter(user=user, activo=True)
    inversiones_finalizadas = Investment.objects.filter(user=user, activo=False)
    total_inversiones_activas = sum(inv.amount for inv in inversiones_activas)

    # Obtener tareas completadas hoy
    tareas_completadas_hoy = TareaUsuario.objects.filter(
        usuario=user, fecha_asignacion__date=hoy, completado=True
    ).count()

    # Determinar si puede hacer más tareas
    puede_hacer_tarea = tareas_completadas_hoy < MAX_TAREAS_DIARIAS

    context = {
        'user': user,
        'balance': user.balance,  # Mostramos el balance del usuario directamente desde CustomUser
        'total_inversiones_activas': total_inversiones_activas,
        'inversiones': inversiones_activas,
        'cantidad_activas': inversiones_activas.count(),
        'cantidad_finalizadas': inversiones_finalizadas.count(),
        'tareas_completadas_hoy': tareas_completadas_hoy,
        'tareas_disponibles': MAX_TAREAS_DIARIAS - tareas_completadas_hoy,  # Tareas disponibles para completar
        'puede_hacer_tarea': puede_hacer_tarea,
        'es_vip': user.is_vip,
        'vip_expiracion': user.vip_expiration,
        'solicitudes_vip_pendientes': SolicitudVIP.objects.filter(user=user, estado='pendiente'),
        'referidos': referidos,  # Referidos activos del usuario
        'deposito_pendiente': deposito_pendiente  # Agregar depósito pendiente al contexto
    }

    return render(request, 'dashboard.html', context)


# ==========================
# RETIRAR INVESTMENT
# ==========================
@login_required
def retirar_investment(request, investment_id):
    if request.method == 'POST':
        investment = get_object_or_404(Investment, id=investment_id, user=request.user, activo=True)
        investment.activo = False
        investment.save()
        messages.success(request, "Investment retirada con éxito.")
    else:
        messages.error(request, "Método no permitido.")
    return redirect('dashboard')

# ==========================
# JUEGOS
# ==========================
@login_required
def iniciar_juego(request, juego_id):
    profile = request.user.profile

    # Mapeo de tipos de juego
    tipos_juego = {1: 'Ruleta', 2: 'Cartas', 3: 'Tragamonedas'}
    juego_tipo = tipos_juego.get(juego_id)
    
    if not juego_tipo:
        messages.error(request, "Juego no válido.")
        return redirect('juegos')

    if profile.balance < JUEGO_COSTO:
        messages.error(request, "Saldo insuficiente para jugar.")
        return redirect('juegos')

    hoy = timezone.now().date()
    juegos_hoy = JuegoInvestment.objects.filter(usuario=request.user, fecha_juego__date=hoy).count()
    
    if juegos_hoy >= MAX_JUEGOS_DIARIOS:
        messages.warning(request, f"Máximo de {MAX_JUEGOS_DIARIOS} juegos diarios alcanzado.")
        return redirect('juegos')

    # Restar el costo del juego al balance del perfil
    profile.balance -= JUEGO_COSTO
    profile.save()

    # Crear la inversión
    investment = Investment.objects.create(user=request.user, amount=JUEGO_COSTO, activo=True)

    # Crear el juego de inversión
    juego = JuegoInvestment.objects.create(
        usuario=request.user,
        investment=investment,
        tipo_juego=juego_tipo,
        fecha_juego=timezone.now()
    )

    messages.success(request, f"¡Juego de {juego_tipo} iniciado!")
    return redirect('jugar_inversion', juego_id=juego.id)

@login_required
def jugar_juego(request, tipo_juego):
    # Lógica de juego según el tipo_juego
    if tipo_juego == 'ruleta':
        return render(request, 'juegos/ruleta.html')
    elif tipo_juego == 'cartas':
        return render(request, 'juegos/cartas.html')  # Asegúrate de tener la plantilla
    elif tipo_juego == 'tragamonedas':
        return render(request, 'juegos/tragamonedas.html')  # Asegúrate de tener la plantilla
    else:
        return render(request, 'juegos/error.html', {'mensaje': 'Tipo de juego no encontrado'})

@login_required
def jugar_para_ganar(request):
    return render(request, 'juegos/jugar_para_ganar.html')

@login_required
def jugar_inversion(request, juego_id):
    # Obtenemos el juego de inversión por su ID
    juego = get_object_or_404(JuegoInvestment, id=juego_id, usuario=request.user)
    
    # Aquí puedes agregar la lógica que maneja el juego (por ejemplo, si el usuario ganó o perdió)
    return render(request, 'juegos/jugar_inversion.html', {'juego': juego})

@login_required
def resultado_juego(request, juego_id):
    juego = get_object_or_404(JuegoInvestment, id=juego_id, usuario=request.user)

    # Simulamos el resultado del juego
    sobre_ganador = str(random.randint(1, 6))  # Número aleatorio entre 1 y 6
    juego.sobre_ganador = sobre_ganador
    juego.sobre_elegido = request.POST.get('sobre_elegido')

    # Comprobamos si el jugador ganó
    if juego.sobre_elegido == juego.sobre_ganador:
        juego.resultado = 'ganado'
    else:
        juego.resultado = 'perdido'

    juego.save()

    return render(request, 'juegos/resultado_juego.html', {'juego': juego})


# ==========================
# EDITAR PERFIL
# ==========================
@login_required
def editar_perfil(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('perfil')
        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        profile_form = UserProfileForm(instance=profile)

    return render(request, 'perfil/editar_perfil.html', {'profile_form': profile_form})

# En views.py
@login_required
def perfil_actualizar_foto(request):
    if request.method == 'POST' and request.FILES.get('foto'):
        try:
            user = request.user
            profile = user.profile
            foto = request.FILES['foto']

            # Verificar si el archivo es una imagen
            if foto.content_type not in ['image/jpeg', 'image/png', 'image/gif']:
                return JsonResponse({'status': 'error', 'message': 'El archivo debe ser una imagen (JPEG, PNG, GIF).'}, status=400)

            # Guardar la foto
            profile.photo = foto
            profile.save()

            return JsonResponse({'status': 'ok', 'nueva_foto': profile.photo.url})

        except Exception as e:
            # Log para detectar errores
            print(f"Error al subir la foto: {e}")
            return JsonResponse({'status': 'error', 'message': 'Ocurrió un error al subir la foto. Por favor, intente de nuevo.'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'No se encontró un archivo de imagen.'}, status=400)

@login_required
def perfil_eliminar_foto(request):
    user = request.user
    profile = user.profile

    # Eliminar la foto de perfil
    profile.foto = None
    profile.save()

    messages.success(request, "Foto de perfil eliminada correctamente.")
    return redirect('perfil')

@login_required
def actualizar_campo_perfil(request):
    if request.method == 'POST':
        # Obtener el campo y el valor que se desea actualizar
        field = request.POST.get('field')
        value = request.POST.get('value')

        if field and value is not None:
            # Actualizar los campos del perfil basándonos en el 'field'
            user = request.user
            profile = user.profile

            if field == 'first_name':
                user.first_name = value
            elif field == 'last_name':
                user.last_name = value
            elif field == 'phone':
                profile.phone = value
            elif field == 'links':
                profile.links = value
            elif field == 'bio':
                profile.bio = value

            # Guardamos los cambios
            user.save()
            profile.save()

            return JsonResponse({'status': 'ok'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Datos incorrectos'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

# ==========================
# CAMBIO DE CONTRASEÑA
# ==========================
@login_required
def cambiar_contraseña(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Contraseña cambiada correctamente.")
            
            # Redirige a la página anterior o al panel de inicio si no hay página anterior
            return redirect(request.META.get('HTTP_REFERER', 'inicio'))
        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'usuarios/cambiar_contraseña.html', {'form': form})



# ==========================
# DEPÓSITOS
# ==========================
@login_required
def crear_deposito(request):
    deposito = None
    error_message = None

    if request.method == 'POST':
        monto = Decimal(request.POST.get('monto', 0))
        if monto <= 0:
            messages.error(request, "Monto inválido.")
            return redirect('deposito')  # Redirige si el monto es inválido

        # Crear el depósito
        deposito = CryptoDeposit.objects.create(
            user=request.user,
            payment_id=f"DEP-{random.randint(100000, 999999)}",
            amount_usd=monto,
            status='pending'
        )

        # Crear una transacción para el depósito
        transaccion = Transaccion.objects.create(
            user=request.user,
            tipo='deposito',
            monto=monto,
            descripcion=f"Depósito en plataforma - ID {deposito.payment_id}"
        )

        request.user.balance += monto
        request.user.save()

        messages.success(request, f"Depósito creado. Monto pendiente: ${monto:.2f}")
        return redirect('direccion_pago', deposito_id=deposito.id)  # Redirige al siguiente paso

    return render(request, 'deposito/crear.html', {'deposito': deposito, 'error_message': error_message})


@login_required
def depositos_view(request):
    # Obtener los depósitos del usuario
    user_depositos = CryptoDeposit.objects.filter(user=request.user)
    return render(request, 'deposito/depositos.html', {'depositos': user_depositos})

# ==========================
# WEBHOOK NOWPAYMENTS
# ==========================
def verificar_firma(payload, firma_enviada):
    secret_key = settings.NOWPAYMENTS_API_SECRET_KEY  # Asegúrate de que esta sea la clave secreta correcta
    mensaje = json.dumps(payload, sort_keys=True).encode('utf-8')
    firma_calculada = hmac.new(secret_key.encode('utf-8'), mensaje, hashlib.sha256).hexdigest()
    return firma_enviada == firma_calculada


@csrf_exempt  # Si decides permitir algún webhook o API externa
def webhook_interno(request):
    if request.method == 'POST':
        try:
            # Aquí recibirías datos de algún sistema externo (si aplica)
            payload = json.loads(request.body)
            payment_id = payload.get('payment_id')
            status = payload.get('status')

            if not payment_id or not status:
                return JsonResponse({'error': 'Faltan datos en el webhook'}, status=400)

            # Buscar el depósito en la base de datos
            deposito = CryptoDeposit.objects.get(payment_id=payment_id)

            if status == 'confirmado':  # Status simulado
                deposito.status = 'confirmed'
                deposito.save()
                # Crear una notificación para el usuario
                Notification.objects.create(
                    user=deposito.user,
                    message=f"Tu depósito con ID {payment_id} ha sido confirmado."
                )
                return JsonResponse({'status': 'success', 'message': 'Depósito confirmado.'}, status=200)
            elif status == 'fallido':
                deposito.status = 'failed'
                deposito.save()
                # Crear una notificación para el usuario
                Notification.objects.create(
                    user=deposito.user,
                    message=f"Tu depósito con ID {payment_id} ha fallado."
                )
                return JsonResponse({'status': 'success', 'message': 'Depósito fallido.'}, status=200)

            return JsonResponse({'error': 'Estado de pago desconocido'}, status=400)

        except CryptoDeposit.DoesNotExist:
            return JsonResponse({'error': 'Depósito no encontrado'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Error al procesar el JSON del webhook'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Ocurrió un error: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

# ==========================
# OBTENER NOTIFICACIONES
# ==========================
def obtener_notificaciones(request):
    if request.user.is_authenticated:
        notificaciones = Notification.objects.filter(user=request.user, is_read=False)
        notifications_data = [{"message": notif.message} for notif in notificaciones]
        return JsonResponse({"notificaciones": notifications_data})
    return JsonResponse({"error": "Usuario no autenticado"}, status=401)


def execute_tron_transaction(from_address, to_address, amount):
    """Llamar el script Node.js para realizar la transferencia de TRC20 USDT."""
    command = [
        'node', 'tron_backend.js', from_address, to_address, str(amount)
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        return True
    else:
        print(f"Error al ejecutar la transacción: {result.stderr.decode()}")
        return False
    
@login_required
def withdraw_view(request):
    try:
        wallet = Wallet.objects.get(user=request.user)  # Obtener la billetera del usuario
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user)
        messages.warning(request, "Tu billetera ha sido creada. Por favor, intenta nuevamente.")
        return redirect('retiros')

    if request.method == 'POST':
        form = CryptoWithdrawForm(request.POST, user=request.user)

        if form.is_valid():
            amount_usd = form.cleaned_data['amount_usd']
            wallet_address = form.cleaned_data['wallet_address']

            if wallet.balance >= amount_usd:
                # Aquí llamamos a la función para enviar USDT a la dirección TRC20 del usuario
                from_address = wallet.address  # Dirección interna de la billetera
                success = execute_tron_transaction(from_address, wallet_address, amount_usd)

                if success:
                    # Crear el objeto CryptoWithdraw y actualizar el saldo de la billetera
                    retiro = CryptoWithdraw.objects.create(
                        user=request.user,
                        amount_usd=amount_usd,
                        wallet_address=wallet_address,
                        status='pending',
                    )
                    wallet.balance -= amount_usd
                    wallet.save()

                    messages.success(request, f"Retiro de ${amount_usd} solicitado correctamente.")
                    return redirect('retiros_status')
                else:
                    messages.error(request, "Hubo un error al procesar el retiro.")
            else:
                messages.error(request, "Saldo insuficiente para realizar el retiro.")
    else:
        form = CryptoWithdrawForm(user=request.user)

    return render(request, 'retiro/solicitar.html', {'form': form})


def invertir_ajax(request):
    # Lógica de la función (ejemplo)
    return JsonResponse({"status": "success", "message": "Inversión exitosa"})

def perfil_view(request):
    # Lógica para la vista de perfil
    return render(request, 'perfil.html')

def ajax_actualizar_perfil(request):
    # Lógica para actualizar el perfil de usuario mediante AJAX
    return JsonResponse({"message": "Perfil actualizado"})

# Vista para iniciar el depósito
@login_required
def deposito_inicio(request):
    # Lógica para iniciar el depósito
    return render(request, 'deposito/inicio.html')

# Vista para mostrar la dirección de pago del depósito
@login_required
def deposito_direccion_pago(request):
    # Lógica para mostrar la dirección de pago (esto depende de tu implementación)
    return render(request, 'deposito/direccion_pago.html')

# Vista para capturar detalles del depósito
@login_required
def deposito_captura(request):
    if request.method == 'POST':
        # Lógica para procesar los datos del depósito
        monto = request.POST.get('monto')
        # Puedes agregar más lógica dependiendo de cómo manejes la captura

        # Suponiendo que el depósito se marca como 'pendiente'
        deposito = CryptoDeposit.objects.create(
            user=request.user,
            amount_usd=monto,
            status='pending'
        )

        messages.success(request, "Depósito capturado con éxito.")
        return redirect('estado_deposito')  # Redirige al estado del depósito

    return render(request, 'deposito/captura.html')

@login_required
def solicitar_retiro(request):
    if request.method == 'POST':
        # Lógica para manejar el retiro, como verificar el monto, procesar la solicitud, etc.
        monto = request.POST.get('monto')
        if monto and float(monto) > 0:
            # Aquí puedes agregar el código para procesar el retiro
            messages.success(request, "Solicitud de retiro procesada correctamente.")
        else:
            messages.error(request, "Monto inválido o no proporcionado.")
        
    return render(request, 'retiro/solicitar_retiro.html')

@login_required
def retiros_aprobados_view(request):
    # Filtrar los retiros aprobados
    retiros_aprobados = Retiro.objects.filter(user=request.user, estado='aprobado')

    return render(request, 'retiro/retiros_aprobados.html', {'retiros_aprobados': retiros_aprobados})

@login_required
def retiros_status_view(request):
    # Obtener todos los retiros del usuario con su estado
    retiros = Retiro.objects.filter(user=request.user)

    # Puedes filtrar y categorizar por el estado del retiro
    pendientes = retiros.filter(estado='pendiente')
    aprobados = retiros.filter(estado='aprobado')
    rechazados = retiros.filter(estado='rechazado')

    return render(request, 'retiro/retiros_status.html', {
        'pendientes': pendientes,
        'aprobados': aprobados,
        'rechazados': rechazados
    })

@login_required
def lista_vip_view(request):
    # Obtener todos los usuarios VIP (o alguna otra lógica relacionada con VIP)
    usuarios_vip = UsuarioVIP.objects.all()  # O filtra por alguna condición relevante

    return render(request, 'vip/lista_vip.html', {
        'usuarios_vip': usuarios_vip
    })

@login_required
def desbloquear_vip(request, vip_id):
    vip = get_object_or_404(UsuarioVIP, id=vip_id)
    
    # Lógica para desbloquear el VIP (esto puede incluir cambiar un campo de estatus, etc.)
    vip.status = 'desbloqueado'  # Asegúrate de que tu modelo tenga un campo 'status' o algo similar
    vip.save()

    # Redirigir a la página que desees, por ejemplo:
    return redirect('lista_vip')  # Asegúrate de que esta vista esté definida

# Vista para solicitar un VIP
@login_required
def solicitar_vip(request, vip_id):
    vip = get_object_or_404(UsuarioVIP, id=vip_id)

    # Aquí puedes agregar lógica para cambiar el estado del VIP
    # Por ejemplo, cambiar el estado a 'pendiente' o realizar alguna validación adicional
    vip.status = 'pendiente'  # Esto depende de cómo tengas configurado el modelo
    vip.save()

    # Redirigir a una vista de éxito o alguna otra vista donde muestres el estado de la solicitud
    return redirect('lista_vip')  # Asegúrate de que esta vista esté definida

@login_required
def comprar_vip_view(request):
    if request.method == 'POST':
        nivel = request.POST.get('nivel', '')  # Asegúrate de obtener el nivel de la solicitud

        if not nivel:
            messages.error(request, "Nivel VIP no especificado.")
            return redirect('comprar_vip')

        # Lógica para comprar VIP, como crear un nuevo objeto UsuarioVIP
        vip = UsuarioVIP.objects.create(
            user=request.user,
            nivel=nivel,
            status='solicitado',  # O 'pendiente' según cómo manejes los estados
        )

        # Redirigir a una página de confirmación o success
        messages.success(request, f"¡VIP {nivel} comprado con éxito!")
        return redirect('vip_levels')  # Asegúrate de que esta vista esté definida

    # Si no es POST, renderizamos el formulario de compra VIP
    return render(request, 'vip/comprar_vip.html')

@login_required
def vip_levels_view(request):
    # Obtiene los niveles VIP disponibles (puedes personalizar según tu modelo)
    niveles_disponibles = ['VIP 1', 'VIP 2', 'VIP 3']  # Ejemplo de niveles
    vip_usuario = UsuarioVIP.objects.filter(user=request.user).first()

    # Si el usuario tiene un nivel VIP, lo mostramos
    if vip_usuario:
        vip_info = f"Nivel VIP: {vip_usuario.nivel} - Estado: {vip_usuario.status}"
    else:
        vip_info = "No tienes nivel VIP."

    return render(request, 'vip_levels.html', {
        'niveles_disponibles': niveles_disponibles,
        'vip_info': vip_info,
    })

@login_required
def tareas_diarias_view(request):
    # Obtener las tareas diarias del usuario
    tareas = Tarea.objects.filter(usuario=request.user, completada=False)

    return render(request, 'tareas/tareas_diarias.html', {
        'tareas': tareas
    })

@login_required
def realizar_tarea(request, tarea_id):
    # Obtener la tarea específica
    tarea = get_object_or_404(Tarea, id=tarea_id, usuario=request.user, completada=False)

    # Si la solicitud es POST, marcar la tarea como completada
    if request.method == 'POST':
        tarea.completada = True
        tarea.save()

        # Redirigir a una página de éxito o volver a la lista de tareas diarias
        return redirect('tareas_diarias')

    return render(request, 'realizar_tarea.html', {'tarea': tarea})

@login_required
def completar_tarea(request, task_id):
    # Obtener la tarea específica
    tarea = get_object_or_404(Tarea, id=task_id, usuario=request.user, completada=False)

    # Marcar la tarea como completada
    tarea.completada = True
    tarea.save()

    # Redirigir al usuario a su historial de tareas o alguna otra vista
    return redirect('historial_tareas')

@login_required
def historial_tareas_view(request):
    # Obtener las tareas completadas por el usuario
    tareas_completadas = Tarea.objects.filter(usuario=request.user, completada=True)

    # Renderizar la vista con las tareas
    return render(request, 'historial.html', {'tareas_completadas': tareas_completadas})

@login_required
def finanzas_view(request):
    # Obtener los depósitos y retiros del usuario
    total_depositos = CryptoDeposit.objects.filter(user=request.user).aggregate(total_depositos=models.Sum('amount_usd'))['total_depositos'] or 0
    total_retiros = CryptoWithdraw.objects.filter(user=request.user).aggregate(total_retiros=models.Sum('amount_usd'))['total_retiros'] or 0
    saldo_actual = total_depositos - total_retiros  # Calculando el saldo actual

    context = {
        'total_depositos': total_depositos,
        'total_retiros': total_retiros,
        'saldo_actual': saldo_actual,
    }

    return render(request, 'finanzas.html', context)

@login_required
def descargar_historial(request):
    # Filtrar las transacciones del usuario
    transacciones = Transaccion.objects.filter(user=request.user)

    # Crear el archivo CSV en memoria
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Tipo', 'Monto', 'Fecha', 'Descripción'])

    # Escribir las transacciones en el CSV
    for transaccion in transacciones:
        writer.writerow([transaccion.tipo, transaccion.monto, transaccion.fecha, transaccion.descripcion])

    # Guardar el CSV en un archivo descargable
    response = JsonResponse({'message': 'Historial descargado correctamente'}, status=200)
    response['Content-Disposition'] = 'attachment; filename="historial_transacciones.csv"'
    response.write(output.getvalue())

    return response

@login_required
def configuracion_view(request):
    # Obtener el perfil del usuario actual (puedes personalizar la lógica aquí)
    user = request.user

    # Aquí puedes agregar lógica para actualizar la configuración del usuario
    # Por ejemplo: Cambiar nombre de usuario, correo, etc.
    
    if request.method == 'POST':
        # Procesar los datos enviados en un formulario
        # Actualizar los campos del usuario, si es necesario
        # Ejemplo de actualización del nombre de usuario:
        new_username = request.POST.get('username')
        if new_username:
            user.username = new_username
            user.save()

        # Puedes agregar más lógica aquí para cambiar otros datos del usuario

    context = {
        'user': user,  # Puedes pasar el objeto `user` al contexto si lo necesitas en el template
    }

    return render(request, 'configuracion.html', context)

@login_required
def referidos_view(request):
    # Obtener los referidos del usuario actual
    user = request.user
    referidos = Referido.objects.filter(referidor=user)

    # Generar el enlace de referido
    link_referido = f"http://127.0.0.1:8000/invitar/{user.id}/?ref={user.username}"

    context = {
        'referidos': referidos,
        'user': user,
        'link_referido': link_referido,  # Pasa el enlace de referido
    }

    return render(request, 'referidos/mis_referidos.html', context)

@login_required
def invitar_view(request, user_id):
    # Obtener al usuario referidor y al usuario referido (por el parámetro 'ref')
    referidor = request.user
    referido_username = request.GET.get('ref')
    
    if not referido_username:
        messages.error(request, "No se proporcionó un usuario de referido.")
        return redirect('dashboard')  # Redirige a una página adecuada si falta el parámetro
    
    # Usamos CustomUser en lugar de User, ya que es el modelo personalizado
    try:
        referido = get_object_or_404(CustomUser, username=referido_username)
    except CustomUser.DoesNotExist:
        messages.error(request, "El usuario referido no existe.")
        return redirect('dashboard')

    # Verificar si ya existe una relación de referido para evitar duplicados
    if Referido.objects.filter(referidor=referidor, usuario=referido).exists():
        messages.info(request, "Este usuario ya ha sido referido.")
        return redirect('dashboard')
    
    # Crear un nuevo registro de referido
    Referido.objects.create(referidor=referidor, usuario=referido)
    
    # (Opcional) Mostrar mensaje de éxito
    messages.success(request, f"¡Bienvenido {referido.username}! Has sido referido por {referidor.username}.")
    
    return redirect('dashboard')  # Redirige a una página de bienvenida o inicio
@login_required
def soporte_view(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        asunto = request.POST.get('asunto')
        mensaje = request.POST.get('mensaje')

        # Validar que ambos campos sean completos
        if not asunto or not mensaje:
            messages.error(request, "El asunto y el mensaje son obligatorios.")
            return render(request, 'soporte.html')

        # Enviar el correo de soporte
        try:
            send_mail(
                f"Solicitud de Soporte: {asunto}",
                mensaje,
                request.user.email,
                [settings.SUPPORT_EMAIL],  # Correo de soporte que definiste en tu configuración
                fail_silently=False,
            )
            messages.success(request, "Tu solicitud de soporte ha sido enviada.")
        except Exception as e:
            messages.error(request, f"Hubo un error al enviar tu solicitud: {str(e)}")

    return render(request, 'soporte.html')

@login_required
def estadisticas(request):
    # Obtener el perfil del usuario
    user_profile = request.user.profile

    # Estadísticas de los depósitos
    total_depositos = CryptoDeposit.objects.filter(user=request.user).count()

    # Estadísticas de los juegos jugados
    juegos_jugados = JuegoInvestment.objects.filter(usuario=request.user).count()

    # Estadísticas de las tareas realizadas
    tareas_completadas = Tarea.objects.filter(usuario=request.user, completada=True).count()  # Usa Tarea en lugar de Task

    # Aquí puedes agregar más estadísticas personalizadas según tu modelo de datos

    context = {
        'total_depositos': total_depositos,
        'juegos_jugados': juegos_jugados,
        'tareas_completadas': tareas_completadas,
        'saldo_actual': user_profile.balance,  # Suponiendo que el perfil tiene un balance
    }

    return render(request, 'estadisticas.html', context)


class UploadPaymentForm(forms.Form):
    txid = forms.CharField(max_length=100)
    captura_pago = forms.ImageField()
    aceptar_terminos = forms.BooleanField()

@login_required
def subir_captura_pago(request, deposito_id):
    deposito = CryptoDeposit.objects.get(id=deposito_id, user=request.user)

    if request.method == 'POST':
        form = UploadPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            txid = form.cleaned_data['txid']

            # Verifica que el TXID no se repita
            if CryptoDeposit.objects.filter(txid=txid).exists():
                messages.error(request, "Este TXID ya ha sido registrado. Por favor, utiliza uno nuevo.")
                return redirect('subir_pago', deposito_id=deposito.id)

            deposito.txid = txid
            deposito.captura_pago = form.cleaned_data['captura_pago']
            deposito.aceptar_terminos = form.cleaned_data['aceptar_terminos']
            deposito.status = 'pending'  # Pendiente hasta revisión administrativa
            deposito.save()

            messages.success(request, "Pago recibido. Se está procesando tu depósito.")
            return redirect('estado_deposito', deposito_id=deposito.id)
    else:
        form = UploadPaymentForm()

    return render(request, 'deposito/subir_pago.html', {'form': form, 'deposito': deposito})

@login_required
def estado_deposito(request, deposito_id):
    deposito = get_object_or_404(CryptoDeposit, id=deposito_id, user=request.user)

    # Mensaje de seguridad y tiempo estimado de revisión
    if deposito.status == 'pending':
        mensaje_seguridad = "Asegúrate de que los detalles del pago sean correctos."
        tiempo_revision = "Estimado en 24 horas."
    elif deposito.status == 'confirmed':
        mensaje_seguridad = "Tu depósito ha sido confirmado. Gracias por tu pago."
        tiempo_revision = "El depósito ha sido confirmado."
    else:
        mensaje_seguridad = "Tu depósito ha sido rechazado. Por favor, contacta con soporte."
        tiempo_revision = "Revisa los detalles y vuelve a intentarlo."

    context = {
        'deposito': deposito,
        'mensaje_seguridad': mensaje_seguridad,
        'tiempo_revision': tiempo_revision,
    }

    return render(request, 'deposito/estado_deposito.html', context)

@login_required
def direccion_pago(request, deposito_id):
    deposito = CryptoDeposit.objects.get(id=deposito_id, user=request.user)
    direccion_pago = 'TTtdsjPMYGmB1spApBR7k4HyU6UEqRq587'  # Se puede obtener dinámicamente si se necesita
    return render(request, 'deposito/direccion_pago.html', {'direccion_pago': direccion_pago, 'deposito': deposito})


@login_required
def inicio(request):
    # Lógica para cargar datos, como balance de usuario u opciones de recarga VIP
    balance = 1000  # Aquí puedes obtener el balance del modelo de usuario o sistema de finanzas
    recargas_vip = [
        {'nombre': 'Recarga VIP 1', 'precio': 50},
        {'nombre': 'Recarga VIP 2', 'precio': 100},
    ]

    return render(request, 'deposito/inicio.html', {'balance': balance, 'recargas_vip': recargas_vip})



def verificar_firma(payload, firma_enviada):
    secret_key = settings.NOWPAYMENTS_API_SECRET_KEY  # La clave secreta de NOWPayments
    mensaje = json.dumps(payload, sort_keys=True).encode('utf-8')
    firma_calculada = hmac.new(secret_key.encode('utf-8'), mensaje, hashlib.sha256).hexdigest()
    return firma_enviada == firma_calculada

@login_required
def finalizar_deposito(request, deposito_id):
    deposito = get_object_or_404(CryptoDeposit, id=deposito_id, user=request.user)

    if request.method == 'POST':
        # Finalizamos el depósito como 'confirmed' y guardamos la fecha
        deposito.status = 'confirmed'
        deposito.fecha_confirmacion = timezone.now()
        deposito.save()

        # Crear una transacción de ganancia para el usuario (si es aplicable)
        Transaccion.objects.create(
            user=request.user,
            tipo='deposito',
            monto=deposito.amount_usd,
            descripcion=f"Depósito confirmado - ID {deposito.payment_id}"
        )

        messages.success(request, "Tu depósito ha sido confirmado. Puedes ver el estado de tu depósito.")
        return redirect('informacion_deposito', deposito_id=deposito.id)  # Redirige a la página de estado de depósito

    return render(request, 'deposito/finalizar.html', {'deposito': deposito})

@login_required
def informacion_deposito(request, deposito_id):
    deposito = get_object_or_404(CryptoDeposit, id=deposito_id, user=request.user)

    # Mensaje de seguridad y tiempo estimado de revisión
    if deposito.status == 'pending':
        mensaje_seguridad = "Asegúrate de que los detalles del pago sean correctos."
        tiempo_revision = "Estimado en 24 horas."
    elif deposito.status == 'confirmed':
        mensaje_seguridad = "Tu depósito ha sido confirmado. Gracias por tu pago."
        tiempo_revision = "El depósito ha sido confirmado."
    else:
        mensaje_seguridad = "Tu depósito ha sido rechazado. Por favor, contacta con soporte."
        tiempo_revision = "Revisa los detalles y vuelve a intentarlo."

    context = {
        'deposito': deposito,
        'mensaje_seguridad': mensaje_seguridad,
        'tiempo_revision': tiempo_revision,
    }

    return render(request, 'deposito/estado_deposito.html', context)

def fallar_deposito(request, id):
    try:
        deposito = CryptoDeposit.objects.get(id=id)

        if deposito.status == 'pending':
            deposito.status = 'failed'
            deposito.save()
            messages.success(request, "Depósito marcado como fallido.")
        else:
            messages.error(request, "Este depósito ya no está pendiente.")
    
    except CryptoDeposit.DoesNotExist:
        messages.error(request, "Este depósito no existe o ha sido eliminado.")
    
    # Redirige a la lista de depósitos del panel de administración
    return redirect('admin:inversiones_cryptodeposit_changelist')


def confirmar_deposito(request, id):
    try:
        deposito = CryptoDeposit.objects.get(id=id)

        if deposito.status == 'pending':
            deposito.status = 'confirmed'
            deposito.confirmed_at = timezone.now()
            deposito.save()

            # Actualizar la billetera interna del usuario
            wallet = get_object_or_404(Wallet, user=deposito.user)

            # Asegúrate de que el monto del depósito sea adecuado
            wallet.balance += deposito.amount_usd  # Agregar el monto en USD a la billetera interna
            wallet.save()

            messages.success(request, f"Depósito de ${deposito.amount_usd} confirmado con éxito.")
        else:
            messages.error(request, "Este depósito ya ha sido procesado o no está pendiente.")
    
    except CryptoDeposit.DoesNotExist:
        messages.error(request, "Este depósito no existe o ha sido eliminado.")
    
    # Redirige a la lista de depósitos del panel de administración
    return redirect('admin:inversiones_cryptodeposit_changelist')
# views.py


def ver_balance(request):
    wallet = request.user.wallet
    return render(request, 'wallet_balance.html', {'wallet': wallet})
