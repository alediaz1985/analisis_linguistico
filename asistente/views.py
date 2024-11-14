import os
import re  # Asegúrate de que el módulo re esté importado
import spacy
from django.shortcuts import render
import speech_recognition as sr
from pydub import AudioSegment
from googletrans import Translator

# Inicializar el modelo de spacy para español y el traductor de Google
nlp = spacy.load("es_core_news_sm")
translator = Translator()

# Procesamiento de audio para reconocimiento de voz
def reconocimiento_voz(request):
    audio_file = request.FILES['audio']
    audio_path = f"temp_{audio_file.name}"

    with open(audio_path, 'wb') as f:
        f.write(audio_file.read())

    if not audio_path.endswith('.wav'):
        audio = AudioSegment.from_file(audio_path)
        audio.export("temp_audio.wav", format="wav")
        os.remove(audio_path)
        audio_path = "temp_audio.wav"

    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        texto = recognizer.recognize_google(audio, language='es-ES')
    except sr.UnknownValueError:
        texto = "No se pudo entender el audio."
    except sr.RequestError:
        texto = "Error en la conexión con el servicio de reconocimiento de voz."

    os.remove(audio_path)
    return texto

# Procesamiento del archivo de texto
def leer_archivo_texto(file):
    return file.read().decode('utf-8')

# Traducción completa del texto
def traducir_texto(texto, dest='en'):
    try:
        traduccion = translator.translate(texto, dest=dest)
        return traduccion.text
    except Exception:
        return texto

# Clasificación de palabras en función de su tipo gramatical usando Spacy
def clasificar_palabras_por_tipo(texto):
    doc = nlp(texto)
    clasificacion = {
        'sustantivos': [token.text for token in doc if token.pos_ == 'NOUN'],
        'adjetivos': [token.text for token in doc if token.pos_ == 'ADJ'],
        'verbos': [token.text for token in doc if token.pos_ == 'VERB'],
        'adverbios': [token.text for token in doc if token.pos_ == 'ADV']
    }
    return clasificacion

# Vista principal para traducción y categorización de palabras
def analizar(request):
    resultado = {}
    pasos = []  # Lista de pasos a mostrar en la interfaz
    texto = ""

    if request.method == 'POST':
        # Paso 1: Recepción del Texto
        if 'texto' in request.POST and request.POST['texto']:
            texto = request.POST['texto']
            pasos.append("Texto ingresado manualmente.")
        
        elif 'audio' in request.FILES:
            texto = reconocimiento_voz(request)
            pasos.append("Texto recibido mediante reconocimiento de voz.")
        
        elif 'archivo_texto' in request.FILES:
            archivo_texto = request.FILES['archivo_texto']
            texto = leer_archivo_texto(archivo_texto)
            pasos.append("Texto cargado desde archivo.")
        
        resultado['texto'] = texto
        pasos.append(f"Texto procesado: {texto}")

        # Paso 2: Traducción completa del texto
        idioma_origen = 'es' if re.search(r'[a-zA-Z]', texto) else 'en'
        idioma_destino = 'en' if idioma_origen == 'es' else 'es'
        
        texto_traducido = traducir_texto(texto, dest=idioma_destino)
        resultado['texto_traducido'] = texto_traducido
        pasos.append(f"Texto traducido al {'inglés' if idioma_destino == 'en' else 'español'}: {texto_traducido}")

        # Paso 3: Clasificación de Palabras por Tipo
        clasificacion = clasificar_palabras_por_tipo(texto)
        resultado['clasificacion'] = clasificacion
        pasos.append("Clasificación de palabras completada.")

    return render(request, 'asistente/analizar.html', {'resultado': resultado, 'pasos': pasos})
