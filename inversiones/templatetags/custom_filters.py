from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """
    Multiplica dos valores para usar en templates.
    Ejemplo: {{ valor1|mul:valor2 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
