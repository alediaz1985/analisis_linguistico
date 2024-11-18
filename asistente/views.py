import os
import re
import spacy
from django.shortcuts import render
import speech_recognition as sr
from pydub import AudioSegment
from googletrans import Translator
from collections import Counter


from django.shortcuts import render, get_object_or_404, redirect

from .models import Analisis  

from gtts import gTTS
from django.http import HttpResponse

# Inicializar el modelo de spaCy para español y el traductor de Google
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

# Traducción automática con detección de idioma
def traducir_texto(texto):
    """
    Detecta el idioma del texto y lo traduce automáticamente al inglés si está en español,
    o al español si está en inglés.
    """
    if not texto or texto.strip() == "":
        return "El texto está vacío o no es válido para traducir."
    
    try:
        # Detectar el idioma del texto
        idioma_detectado = translator.detect(texto).lang

        # Configurar idioma de destino
        if idioma_detectado == 'es':
            idioma_destino = 'en'  # Traducir al inglés
        elif idioma_detectado == 'en':
            idioma_destino = 'es'  # Traducir al español
        else:
            return texto  # Devuelve el texto original si no es español o inglés

        # Realizar la traducción
        traduccion = translator.translate(texto, src=idioma_detectado, dest=idioma_destino)
        return traduccion.text
    except Exception as e:
        print(f"Error en la traducción: {str(e)} | Texto: {texto}")
        return "Hubo un problema al traducir el texto."

# Clasificación de palabras en función de su tipo gramatical usando spaCy
def clasificar_palabras_por_tipo(texto):
    doc = nlp(texto)
    clasificacion = {
        'sustantivos': [token.text for token in doc if token.pos_ == 'NOUN'],
        'adjetivos': [token.text for token in doc if token.pos_ == 'ADJ'],
        'verbos': [token.text for token in doc if token.pos_ == 'VERB'],
        'adverbios': [token.text for token in doc if token.pos_ == 'ADV']
    }
    return clasificacion

# Contar la frecuencia de cada palabra en el texto
def contar_frecuencia_palabras(texto):
    doc = nlp(texto.lower())
    palabras = [token.text for token in doc if not token.is_punct and not token.is_stop]
    frecuencia = Counter(palabras).most_common()
    return frecuencia

# Vista principal para traducción, categorización y frecuencia de palabras
def analizar(request):
    resultado = {}
    pasos = []  # Lista de pasos a mostrar en la interfaz
    texto = ""

    if request.method == 'POST':
        # Determinar el origen del texto
        dictado = request.POST.get("dictado", "false") == "true"  # Verificar si fue dictado
        origen = None

        if 'audio' in request.FILES:  # Archivo de audio
            texto = reconocimiento_voz(request)
            origen = "archivo de audio"
            pasos.append("Texto recibido mediante reconocimiento de voz (archivo de audio).")
        elif 'archivo_texto' in request.FILES:  # Archivo de texto
            texto = leer_archivo_texto(request.FILES['archivo_texto'])
            origen = "archivo de texto"
            pasos.append("Texto cargado desde archivo de texto.")
        elif dictado:  # Texto dictado
            texto = request.POST['texto']
            origen = "dictado por voz"
            pasos.append("Texto dictado por voz.")
        elif 'texto' in request.POST and request.POST['texto']:  # Texto manual
            texto = request.POST['texto']
            origen = "texto ingresado manualmente"
            pasos.append("Texto ingresado manualmente.")
        else:  # Ninguna fuente válida
            pasos.append("No se recibió ningún texto válido para procesar.")
            return render(request, 'asistente/analizar.html', {'resultado': resultado, 'pasos': pasos})

        # Validar que el texto no esté vacío
        if not texto.strip():
            pasos.append("El texto recibido está vacío o no es válido para procesar.")
            return render(request, 'asistente/analizar.html', {'resultado': resultado, 'pasos': pasos})

        # Procesamiento del texto
        resultado['texto'] = texto
        pasos.append(f"Texto procesado desde: {origen}")

        # Traducción automática
        try:
            texto_traducido = traducir_texto(texto)
            resultado['texto_traducido'] = texto_traducido
            pasos.append("Texto traducido automáticamente.")
        except Exception as e:
            pasos.append(f"Error durante la traducción automática: {e}")
            texto_traducido = "No fue posible realizar la traducción."

        # Clasificación de palabras
        clasificacion = clasificar_palabras_por_tipo(texto)
        resultado['clasificacion'] = clasificacion
        pasos.append("Clasificación de palabras completada.")

        # Conteo de frecuencia de palabras
        frecuencia_palabras = contar_frecuencia_palabras(texto)
        resultado['frecuencia_palabras'] = frecuencia_palabras
        pasos.append("Frecuencia de palabras calculada.")

        # Tokenización
        nivel_tokenizacion = request.POST.get("nivel_tokenizacion", "palabra")
        tokens = tokenizar_texto(texto, nivel=nivel_tokenizacion)
        resultado['tokens'] = tokens
        pasos.append(f"Tokenización completada a nivel: {nivel_tokenizacion.capitalize()}.")
        

        # Guardar los resultados en la base de datos
        Analisis.objects.create(
            texto=texto,
            #palabras_frecuentes=frecuencia_palabras,
            palabras_frecuentes=dict(frecuencia_palabras),  
            categorias_lexicas=clasificacion,
            relaciones_semanticas={"traduccion": texto_traducido},
            tokens=tokens
        )
        pasos.append("Resultados guardados en la base de datos.")

    return render(request, 'asistente/analizar.html', {'resultado': resultado, 'pasos': pasos})
#generar audio mp3

# Nueva vista para generar el archivo de audio
def generar_audio_mp3(request):
    texto = request.POST.get("texto", "")
    if not texto:
        return HttpResponse("No se ha proporcionado texto para generar el audio.", status=400)

    # Ruta para el archivo MP3 en la carpeta estática
    ruta_audio = 'static/asistente/audio/'
    archivo_mp3 = os.path.join(ruta_audio, 'texto_generado.mp3')

    # Crear la carpeta si no existe
    if not os.path.exists(ruta_audio):
        os.makedirs(ruta_audio)

    # Generar el archivo de audio
    try:
        tts = gTTS(text=texto, lang='es')
        tts.save(archivo_mp3)
        return HttpResponse(archivo_mp3)
    except Exception as e:
        return HttpResponse(f"Error al generar el archivo de audio: {e}", status=500)
    

# Vista para mostrar los análisis guardados y seleccionar uno para visualizar
def consultar_analisis(request):
    # Obtener todos los análisis disponibles
    analisis_list = Analisis.objects.all()
    
    # Si se seleccionó un análisis específico, obtener sus detalles
    analisis_id = request.GET.get('analisis_id')
    analisis_seleccionado = None
    error_message = None

    if analisis_id:
        try:
            analisis_seleccionado = Analisis.objects.get(id=analisis_id)

            # Verificar que todos los campos estén correctamente guardados
            if not analisis_seleccionado.texto or not analisis_seleccionado.palabras_frecuentes or not analisis_seleccionado.categorias_lexicas:
                error_message = "Los datos del análisis están incompletos. Por favor, verifique el análisis seleccionado."
                
        except Analisis.DoesNotExist:
            error_message = "El análisis seleccionado no existe."

    context = {
        'analisis_list': analisis_list,
        'analisis_seleccionado': analisis_seleccionado,
        'error_message': error_message
    }
    return render(request, 'asistente/consultar_analisis.html', context)


def tokenizar_texto(texto, nivel="palabra"):
    """
    Tokeniza el texto según el nivel especificado.
    
    Args:
        texto (str): El texto a tokenizar.
        nivel (str): Nivel de tokenización ("palabra", "caracter", "subpalabra").
    
    Returns:
        list: Lista de tokens según el nivel de granularidad.
    """
    if not texto or texto.strip() == "":
        return ["El texto está vacío o no es válido para tokenizar."]
    
    if nivel == "palabra":
        # Tokenización por palabras utilizando spaCy
        doc = nlp(texto)
        tokens = [token.text for token in doc if not token.is_punct and not token.is_space]
    elif nivel == "caracter":
        # Tokenización por caracteres
        tokens = list(texto)
    elif nivel == "subpalabra":
        # Tokenización por subpalabras usando un enfoque simple
        doc = nlp(texto)
        tokens = [token.text[:len(token.text)//2] + '-' + token.text[len(token.text)//2:] for token in doc if len(token.text) > 1]
    else:
        return ["Nivel de tokenización no reconocido."]
    
    return tokens
