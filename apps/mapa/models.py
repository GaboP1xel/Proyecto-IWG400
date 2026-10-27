from django.db import models


#PARAMETROS PARA LOS DATOS DE CALIDAD DEL AIRE
class MedicionAire(models.Model):
    fuente = models.CharField(max_length=50, default='SINCA')
    estacion = models.CharField(max_length=100)
    parametro = models.CharField(max_length=50)
    valor = models.FloatField()
    unidad = models.CharField(max_length=20, default='ug/m3')
    fecha = models.DateTimeField()
    lat = models.FloatField(help_text="Latitud espacial")
    lon = models.FloatField(help_text="Longitud espacial")

    def __str__(self):
        return f"{self.estacion} - {self.parametro}: {self.valor} {self.unidad}"

    class Meta:
        verbose_name = "Medición de Aire"
        verbose_name_plural = "Mediciones de Aire"
        ordering = ['-fecha']
