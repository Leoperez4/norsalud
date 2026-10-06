import datetime

from django import forms


def _etiqueta(hora, minuto):
    sufijo = "a. m." if hora < 12 else "p. m."
    return f"{(hora % 12) or 12}:{minuto:02d} {sufijo}"


def opciones_de_hora(desde=0, hasta=23, paso=15):
    """Lista de (valor 'HH:MM:00', etiqueta '7:15 a. m.') cada `paso` minutos."""
    opciones = []
    for hora in range(desde, hasta + 1):
        for minuto in range(0, 60, paso):
            opciones.append((f"{hora:02d}:{minuto:02d}:00", _etiqueta(hora, minuto)))
    return opciones


class SelectorHora(forms.Select):
    """Desplegable de horas (cada 15 min) en lugar del campo <input type=time> con scroll."""

    def __init__(self, attrs=None, desde=0, hasta=23, paso=15, extra=()):
        opciones = [("", "— Hora —")] + opciones_de_hora(desde, hasta, paso) + list(extra)
        super().__init__(attrs=attrs, choices=opciones)

    def format_value(self, value):
        if isinstance(value, (datetime.time, datetime.datetime)):
            value = value.strftime("%H:%M:00")
        elif isinstance(value, str) and len(value) == 5:
            value = f"{value}:00"
        return super().format_value(value)

    def agregar_opcion_si_falta(self, valor):
        """Para horarios guardados con minutos fuera de la rejilla (p. ej. 7:10)."""
        if not isinstance(valor, datetime.time):
            return
        clave = valor.strftime("%H:%M:00")
        if clave not in dict(self.choices):
            etiqueta = _etiqueta(valor.hour, valor.minute)
            self.choices = sorted(
                list(self.choices) + [(clave, etiqueta)], key=lambda o: o[0]
            )


class FechaHoraWidget(forms.SplitDateTimeWidget):
    """Fecha (calendario) + hora (desplegable) para fechas límite."""

    def __init__(self, attrs=None):
        # 11:59 p. m. como opción rápida de "fin del día".
        selector = SelectorHora(extra=[("23:59:00", "11:59 p. m.")])
        widgets = [forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"), selector]
        forms.MultiWidget.__init__(self, widgets, attrs)
