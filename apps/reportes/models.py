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
    CATEGORIA_AGUA = "agua"
    CATEGORIA_AIRE = "aire"
    CATEGORIA_RESIDUOS = "residuos"

    CATEGORIAS = [
        (CATEGORIA_AGUA, "Agua"),
        (CATEGORIA_AIRE, "Aire"),
        (CATEGORIA_RESIDUOS, "Residuos Sólidos"),
    ]

    GRAVEDADES = [
        (1, "1 - Leve / Baja"),
        (2, "2 - Moderada / Media"),
        (3, "3 - Crítica / Alta"),
    ]

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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reportes",
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIAS,
        default=CATEGORIA_RESIDUOS,
    )
    problema = models.CharField(
        max_length=120,
        default="General",
        help_text="Subcategoría seleccionada por el usuario",
    )
    gravedad = models.PositiveSmallIntegerField(
        choices=GRAVEDADES,
        default=1,
        help_text="Escala del 1 al 3 (gravedad o cantidad)",
    )
    descripcion = models.TextField(blank=True, default="")
    lat = models.FloatField(help_text="Latitud espacial")
    lon = models.FloatField(help_text="Longitud espacial")
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_VALIDADO,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reporte Ciudadano"
        verbose_name_plural = "Reportes Ciudadanos"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"[{self.get_categoria_display()}] {self.problema} (Nvl {self.gravedad}) - {self.usuario}"


class VotoReporte(models.Model):
    VALOR_LIKE = 1
    VALOR_DISLIKE = -1

    VALORES = [
        (VALOR_LIKE, "Apoyar"),
        (VALOR_DISLIKE, "No apoyar"),
    ]

    reporte = models.ForeignKey(
        ReporteCiudadano,
        on_delete=models.CASCADE,
        related_name="votos",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="votos_reportes",
    )
    valor = models.SmallIntegerField(choices=VALORES)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Voto de Reporte"
        verbose_name_plural = "Votos de Reportes"
        unique_together = ("reporte", "usuario")

    def __str__(self):
        return f"{self.usuario} -> Reporte #{self.reporte_id} ({self.valor})"