from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class ReporteBasura(models.Model):
    ESTADOS_REPORTE = [
        ('pendiente', 'Pendiente'),
        ('resuelto', 'Resuelto'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que registro el reporte"
    )
    ubicacion = models.CharField(
        max_length=255,
        help_text="Direccion o punto de referencia"
    )
    descripcion = models.TextField(
        help_text="Detalles del reporte o tipo de residuo"
    )
    lat = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text="Latitud espacial"
    )
    lon = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text="Longitud espacial"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_REPORTE,
        default='pendiente',
        help_text="Estado actual de la limpieza"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora automatica de creacion"
    )

    def __str__(self):
        return f"Reporte en {self.ubicacion} ({self.get_estado_display()})"

    class Meta:
        verbose_name = "Reporte de Basura"
        verbose_name_plural = "Reportes de Basura"
        ordering = ['-fecha_creacion']