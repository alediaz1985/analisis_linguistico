from django.db import models

class Analisis(models.Model):
    texto = models.TextField()
    palabras_frecuentes = models.JSONField(default=dict)  # Diccionario de palabras frecuentes
    categorias_lexicas = models.JSONField(default=dict)   # Diccionario de categorías léxicas
    relaciones_semanticas = models.JSONField(default=dict)  # Relaciones semánticas adicionales
    tokens = models.JSONField(default=list)  # Lista de tokens generados
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Análisis realizado el {self.fecha.strftime('%Y-%m-%d %H:%M:%S')}"
