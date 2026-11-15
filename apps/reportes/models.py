from django.conf import settings
from django.db import models


class TipoReporte(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Tipo de Reporte"
        verbose_name_plural = "Tipos de Reporte"

    def __str__(self):
        return self.nombre


class ReporteCiudadano(models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_VALIDADO = "validado"
    ESTADO_RECHAZADO = "rechazado"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_VALIDADO, "Validado"),
        (ESTADO_RECHAZADO, "Rechazado"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reportes",
    )
    tipo_reporte = models.ForeignKey(
        TipoReporte,
        on_delete=models.PROTECT,
        related_name="reportes",
    )
    descripcion = models.TextField()
    lat = models.FloatField(help_text="Latitud espacial")
    lon = models.FloatField(help_text="Longitud espacial")
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reporte Ciudadano"
        verbose_name_plural = "Reportes Ciudadanos"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.tipo_reporte} - {self.usuario} ({self.estado})"