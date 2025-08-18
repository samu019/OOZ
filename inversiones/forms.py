from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.contrib.auth import authenticate, get_user_model
import re
from .models import Retiro, Wallet
from .models import CryptoDeposit, generar_direccion_billetera
from .models import Deposito, Retiro
from .models import (
    CryptoDeposit, UserTask, Transaccion, Investment,
    UserProfile, CryptoWithdraw, CustomUser
)

# Obtener modelo usuario personalizado
User = get_user_model()

# Validador de imágenes
image_validator = FileExtensionValidator(allowed_extensions=[
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff'
])

# ==========================
# FORMULARIO DE REGISTRO
# ==========================
class RegistroForm(UserCreationForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'}),
        help_text="Debe tener al menos 8 caracteres, una mayúscula y un número."
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña'}),
    )

    class Meta:
        model = User
        fields = ['username']
        labels = {'username': 'Nombre de usuario'}
        widgets = {'username': forms.TextInput(attrs={'placeholder': 'Nombre de usuario'})}

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError("El nombre de usuario es obligatorio.")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Ya existe un usuario con este nombre.")
        return username

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if not password:
            raise ValidationError('Debe ingresar una contraseña.')
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Debe incluir al menos una letra mayúscula.')
        if not re.search(r'\d', password):
            raise ValidationError('Debe incluir al menos un número.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Las contraseñas no coinciden.")
        return cleaned_data


# ==========================
# FORMULARIO DE LOGIN
# ==========================
class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Nombre de usuario',
            'class': 'form-control'
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': 'Contraseña',
            'class': 'form-control'
        })

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                user_obj = User.objects.get(username=username)
            except User.DoesNotExist:
                user_obj = None

            if user_obj:
                self.user_cache = authenticate(
                    self.request, username=user_obj.username, password=password
                )
                if self.user_cache is None:
                    raise forms.ValidationError(
                        self.error_messages['invalid_login'],
                        code='invalid_login',
                        params={'username': self.fields['username'].label},
                    )
            else:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.fields['username'].label},
                )
        else:
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.fields['username'].label},
            )

        self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


# ==========================
# FORMULARIO DE DEPÓSITO (Crypto)
# ==========================

class CryptoDepositForm(forms.ModelForm):
    class Meta:
        model = CryptoDeposit
        fields = ['amount_usd', 'payment_id', 'amount_crypto']
        widgets = {
            'amount_usd': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monto en USD a depositar'
            }),
            'payment_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ID de pago'
            }),
            'amount_crypto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monto en criptomonedas'
            })
        }

    def clean_amount_usd(self):
        amount = self.cleaned_data['amount_usd']
        if amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor que cero.")
        return amount
    
    def clean_amount_crypto(self):
        amount_crypto = self.cleaned_data.get('amount_crypto', 0)
        if amount_crypto < 0:
            raise forms.ValidationError("El monto de criptomonedas no puede ser negativo.")
        return amount_crypto


# ==========================
# FORMULARIO DE RETIRO (Crypto)
# ==========================
class CryptoWithdrawForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = CryptoWithdraw
        fields = ['amount_usd', 'wallet_address']
        widgets = {
            'amount_usd': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monto a retirar en USD'
            }),
            'wallet_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección de la wallet (TRC20)'
            })
        }

    def clean_wallet_address(self):
        wallet_address = self.cleaned_data['wallet_address']
        if not re.match(r'^T[a-zA-Z0-9]{33}$', wallet_address):
            raise forms.ValidationError("La dirección de billetera no es válida para TRC20 (debe comenzar con 'T' y tener 34 caracteres).")
        return wallet_address

    def clean_amount_usd(self):
        amount = self.cleaned_data['amount_usd']
        if amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor que cero.")
        if self.user and amount > self.user.balance:
            raise forms.ValidationError("Saldo insuficiente.")
        return amount

# ==========================
# FORMULARIO DE PERFIL
# ==========================
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['photo', 'phone', 'birthdate', 'address', 'bio', 'links']


# ==========================
# FORMULARIO DE CAMBIO DE CONTRASEÑA
# ==========================
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


# ==========================
# FORMULARIO DE DEPÓSITO (USD o Cripto)
# ==========================
class DepositoForm(forms.ModelForm):
    class Meta:
        model = Deposito
        fields = ['amount_usd', 'payment_id']
        widgets = {
            'amount_usd': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monto en USD'
            }),
            'payment_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ID de pago'
            })
        }


class RetiroForm(forms.ModelForm):
    class Meta:
        model = Retiro
        fields = ['amount_usd', 'wallet_address']
        widgets = {
            'amount_usd': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.00000001'}),
            'wallet_address': forms.TextInput(attrs={'class': 'form-control'})
        }
    
    # Validación personalizada para el monto
    def clean_amount_usd(self):
        amount = self.cleaned_data.get('amount_usd')
        if amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor que 0.")
        return amount

    # Validación personalizada para la dirección de billetera
    def clean_wallet_address(self):
        address = self.cleaned_data.get('wallet_address')
        # Verificar que la dirección no esté vacía o no sea inválida
        if not address:
            raise forms.ValidationError("La dirección de la billetera es requerida.")
        # Puedes agregar más validaciones aquí, como formato de dirección
        return address

    # Método adicional para validar si el usuario tiene suficiente saldo en su billetera
    def clean(self):
        cleaned_data = super().clean()
        amount_usd = cleaned_data.get('amount_usd')
        user_wallet = Wallet.objects.get(user=self.instance.user)

        # Verificar si el monto solicitado es menor o igual al saldo disponible
        if user_wallet.balance < amount_usd:
            raise forms.ValidationError("No tienes suficiente saldo para realizar este retiro.")

        return cleaned_data

class UploadPaymentForm(forms.Form):
    txid = forms.CharField(max_length=64, required=True, label="TXID", widget=forms.TextInput(attrs={'placeholder': 'Introduce el TXID'}))
    captura_pago = forms.ImageField(required=True, label="Comprobante de Pago")
    aceptar_terminos = forms.BooleanField(required=True, label="He leído y acepto los términos y condiciones")

    def clean(self):
        cleaned_data = super().clean()
        txid = cleaned_data.get("txid")
        captura_pago = cleaned_data.get("captura_pago")
        aceptar_terminos = cleaned_data.get("aceptar_terminos")

        if not aceptar_terminos:
            raise forms.ValidationError("Debes aceptar los términos y condiciones.")
        if not txid or not captura_pago:
            raise forms.ValidationError("Debes subir un comprobante de pago y el TXID.")
        return cleaned_data
