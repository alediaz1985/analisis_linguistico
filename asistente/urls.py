from django.urls import path
from . import views

urlpatterns = [
    path('', views.analizar, name='analizar'),
    path('consultar_analisis/', views.consultar_analisis, name='consultar_analisis'),
    path('generar_audio_mp3/', views.generar_audio_mp3, name='generar_audio_mp3'),
]
