# generar_archivos_s3.py
import os
import random

# Diccionarios de frases para construir textos realistas
FRASES_LIMPIAS = [
    "El desarrollo de sistemas distribuidos requiere un diseño cuidadoso de la tolerancia a fallos.",
    "La computación en la nube ofrece una elasticidad sin precedentes para cargas de trabajo variables.",
    "Lithops permite abstraer la infraestructura de ejecución ejecutando código en hilos o Lambdas.",
    "Es crucial monitorizar el rendimiento de las colas de mensajería para evitar cuellos de botella.",
    "El almacenamiento de objetos como AWS S3 es altamente escalable y duradero.",
    "Mañana continuaremos con las pruebas de integración en el entorno de evaluación.",
    "La arquitectura de microservicios fomenta el desacoplamiento entre componentes del sistema.",
    "Una base de datos en memoria proporciona accesos de lectura y escritura con latencias mínimas."
]

FRASES_CON_INSULTOS = [
    "No me gusta nada tu actitud, eres un tonto integral.",
    "El administrador del sistema es un pesado, siempre está bloqueando los accesos.",
    "Vaya diseño de software más malo, el que lo programó es un auténtico idiota.",
    "Deja de enviar peticiones basura a la cola, eres un bobo.",
    "Ese script está mal optimizado y el resultado es una imbecil solución distribuidora.",
    "No entiendo cómo puedes ser tan tonto de caerte en la misma excepción de código."
]

def generar_coleccion_pruebas(target_dir="./datos_s3_simulado", num_archivos=10):
    # Asegurar que la carpeta existe
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f" Creando directorio de datos: '{target_dir}'")
    else:
        # Limpiar archivos anteriores para no acumular basura de pruebas viejas
        for f in os.listdir(target_dir):
            if f.endswith('.txt'):
                os.remove(os.path.join(target_dir, f))
        print(f" Limpiando archivos antiguos en: '{target_dir}'")

    print(f" Generando {num_archivos} nuevos archivos de texto estructurados...")

    for i in range(1, num_archivos + 1):
        nombre_archivo = f"archivo_{i}.txt"
        ruta_completa = os.path.join(target_dir, nombre_archivo)
        
        # Estructuramos el contenido del archivo de forma aleatoria
        lineas = []
        
        # Decidimos el tipo de archivo de forma probabilística
        tipo_carga = random.choice(["limpio", "sucio", "mixto"])
        
        if tipo_carga == "limpio":
            # Archivo de 4 a 6 líneas totalmente libres de insultos
            lineas = [random.choice(FRASES_LIMPIAS) for _ in range(random.randint(4, 6))]
        elif tipo_carga == "sucio":
            # Archivo enfocado puramente en contener insultos
            lineas = [random.choice(FRASES_CON_INSULTOS) for _ in range(random.randint(3, 5))]
        else:
            # Archivo mixto (líneas limpias e insultos intercalados)
            for _ in range(random.randint(5, 8)):
                origen = random.choice([FRASES_LIMPIAS, FRASES_CON_INSULTOS])
                lineas.append(random.choice(origen))
                
        # Escribir el contenido estructurado en el fichero
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            f.write("\n".join(lineas))
            
    print(f"¡Hecho! 10 archivos listos en '{target_dir}' para alimentar tu MapReduce.")

if __name__ == "__main__":
    generar_coleccion_pruebas()