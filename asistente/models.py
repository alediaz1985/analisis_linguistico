from django.db import models

class Analisis(models.Model):
    texto = models.TextField()
    palabras_frecuentes = models.JSONField()       # Diccionario de palabras frecuentes
    categorias_lexicas = models.JSONField()        # Diccionario de categorías léxicas (sinónimos)
    relaciones_semanticas = models.JSONField()     # Relaciones semánticas adicionales (sinónimos, hipónimos, etc.)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Análisis realizado en {self.fecha}"
