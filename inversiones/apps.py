from django.apps import AppConfig

class InversionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inversiones'

    def ready(self):
        import inversiones.signals
