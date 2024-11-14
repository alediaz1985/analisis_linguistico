from django.urls import path
from . import views

urlpatterns = [
    path('', views.analizar, name='analizar'),
    #path('historial/', views.historial, name='historial'),
    path('generar_audio_mp3/', views.generar_audio_mp3, name='generar_audio_mp3'),
]
