import os
import nltk
from django.shortcuts import render
import speech_recognition as sr
from pydub import AudioSegment
from nltk.corpus import wordnet
from googletrans import Translator
import re

# Configurar el path de nltk_data si es necesario
nltk.data.path.append(r'C:\Users\Usuario\nltk_data')

# Inicializar el traductor de Google
translator = Translator()

# Función para descargar los recursos necesarios
def descargar_recursos_nltk():
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)

    try:
        nltk.data.find('corpora/omw-1.4')
    except LookupError:
        nltk.download('omw-1.4', quiet=True)

descargar_recursos_nltk()

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

# Traducción de una lista de palabras
def traducir_palabras(lista_palabras, dest='es'):
    palabras_traducidas = []
    for palabra in lista_palabras:
        try:
            traduccion = translator.translate(palabra, src='en', dest=dest)
            palabras_traducidas.append(traduccion.text)
        except Exception:
            palabras_traducidas.append(palabra)
    return palabras_traducidas

# Categorización y traducción de palabras
def categorizar_palabras(texto, dest='es'):
    categorias = {}
    palabras = re.findall(r'\b\w+\b', texto.lower(), re.UNICODE)

    for palabra in palabras:
        sinonimos = wordnet.synsets(palabra, lang='spa' if dest == 'es' else 'eng')
        lista_sinonimos = []

        for sinonimo in sinonimos:
            nombre_sinonimo = sinonimo.name().split('.')[0]
            if nombre_sinonimo not in lista_sinonimos:
                lista_sinonimos.append(nombre_sinonimo)

        lista_sinonimos = traducir_palabras(lista_sinonimos, dest=dest)

        if lista_sinonimos:
            categorias[palabra] = {"sinonimos": lista_sinonimos}
    
    return categorias

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

        # Paso 3: Categorización de Palabras
        categorias = categorizar_palabras(texto_traducido, dest=idioma_destino)
        resultado['categorias'] = categorias
        pasos.append("Categorización de palabras completada.")

    return render(request, 'asistente/analizar.html', {'resultado': resultado, 'pasos': pasos})
