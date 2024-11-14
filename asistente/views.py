import os
import nltk
from django.shortcuts import render
import speech_recognition as sr
from pydub import AudioSegment
from collections import Counter
from nltk.corpus import wordnet, stopwords
from googletrans import Translator
import re

# Configurar el path de nltk_data si es necesario (puede cambiar según tu sistema)
nltk.data.path.append(r'C:\Users\Usuario\nltk_data')

# Descargar recursos necesarios si no están disponibles
def descargar_recursos_nltk():
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)

    try:
        nltk.data.find('corpora/omw-1.4')
    except LookupError:
        nltk.download('omw-1.4', quiet=True)

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

# Ejecutar la descarga de recursos al iniciar
descargar_recursos_nltk()

# Crear la lista de stopwords en español
stopwords_es = set(stopwords.words('spanish'))

# Inicializar el traductor de Google
translator = Translator()

# Procesamiento de audio
def reconocimiento_voz(request):
    audio_file = request.FILES['audio']
    audio_path = f"temp_{audio_file.name}"

    # Guarda temporalmente el archivo de audio
    with open(audio_path, 'wb') as f:
        f.write(audio_file.read())

    # Convertir a WAV si es necesario
    if not audio_path.endswith('.wav'):
        audio = AudioSegment.from_file(audio_path)
        audio.export("temp_audio.wav", format="wav")
        os.remove(audio_path)  # Eliminar archivo original si no es WAV
        audio_path = "temp_audio.wav"

    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        texto = recognizer.recognize_google(audio, language='es-ES')
    except sr.UnknownValueError:
        texto = "No se pudo entender el audio. Por favor, intente con otro archivo."
    except sr.RequestError:
        texto = "Error en la conexión con el servicio de reconocimiento de voz."

    # Limpia el archivo temporal después de usarlo
    os.remove(audio_path)
    
    return texto

# Procesamiento del archivo de texto
def leer_archivo_texto(file):
    content = file.read().decode('utf-8')  # Lee el archivo y decodifica a texto
    return content

# Función personalizada para tokenización en español sin `punkt`
def tokenizacion_personalizada(texto):
    # Usa una expresión regular para dividir el texto en palabras
    tokens = re.findall(r'\b\w+\b', texto.lower(), re.UNICODE)
    return tokens

def tokenizacion_y_frecuencia(texto):
    tokens = tokenizacion_personalizada(texto)
    frecuencia_palabras = Counter(tokens)
    return dict(frecuencia_palabras.most_common(10))  # Devuelve las 10 palabras más comunes

# Función para traducir una lista de sinónimos al español
def traducir_sinonimos(lista_sinonimos):
    sinonimos_traducidos = []
    for sinonimo in lista_sinonimos:
        try:
            # Intentar traducir el sinónimo al español
            traduccion = translator.translate(sinonimo, src='en', dest='es')
            sinonimos_traducidos.append(traduccion.text)
        except Exception as e:
            print(f"Error al traducir '{sinonimo}': {e}")
            # Si falla la traducción, añade el sinónimo en el idioma original
            sinonimos_traducidos.append(sinonimo)
    return sinonimos_traducidos

def clasificacion_lexica(texto):
    categorias = {}
    for palabra in tokenizacion_personalizada(texto):
        # Filtrar palabras que son stopwords
        if palabra in stopwords_es:
            continue
        
        sinonimos = wordnet.synsets(palabra, lang='spa')
        lista_sinonimos = []

        for sinonimo in sinonimos:
            nombre_sinonimo = sinonimo.name().split('.')[0]
            # Asegurarse de que no haya duplicados en la lista
            if nombre_sinonimo not in lista_sinonimos:
                lista_sinonimos.append(nombre_sinonimo)

        # Traducir todos los sinónimos a español
        lista_sinonimos = traducir_sinonimos(lista_sinonimos)

        # Solo añadir si hay sinónimos y no están vacíos
        if lista_sinonimos:
            categorias[palabra] = {
                "sinonimos": lista_sinonimos
            }
    
    return categorias

def analizar(request):
    resultado = {}
    texto = ""

    if request.method == 'POST':
        # Verificar si el usuario ingresó texto manualmente
        if 'texto' in request.POST and request.POST['texto']:
            texto = request.POST['texto']
        
        # Verificar si se subió un archivo de audio
        elif 'audio' in request.FILES:
            texto = reconocimiento_voz(request)
        
        # Verificar si se subió un archivo de texto
        elif 'archivo_texto' in request.FILES:
            archivo_texto = request.FILES['archivo_texto']
            texto = leer_archivo_texto(archivo_texto)
        
        # Si tenemos texto, proceder con el análisis
        if texto:
            resultado['texto'] = texto
            resultado['frecuencia'] = tokenizacion_y_frecuencia(texto)
            resultado['lexica'] = clasificacion_lexica(texto)

    return render(request, 'asistente/analizar.html', {'resultado': resultado})
