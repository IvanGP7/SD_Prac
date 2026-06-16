# ejercicio4_batch.py
import os
import sys
import lithops

# =====================================================================
# 1. LÓGICA DE CENSURA (Intacta)
# =====================================================================
INSULTOS = ["tonto", "bobo", "idiota", "imbecil", "pesado"]

def censurar_insultos(texto):
    palabras = texto.split()
    censuradas = []
    contador_insultos = 0
    for palabra in palabras:
        palabra_limpia = palabra.lower().strip(".,!?")
        if palabra_limpia in INSULTOS:
            censuradas.append("****")
            contador_insultos += 1
        else:
            censuradas.append(palabra)
    return " ".join(censuradas), contador_insultos

# =====================================================================
# 2. NUEVA FASE MAP: Ahora recibe una LISTA de archivos (un chunk)
# =====================================================================
def map_filter_insults_batch(lista_archivos, storage):
    """
    Cada Lambda ahora recibe un 'montón' de archivos en vez de uno solo.
    Procesará todos los archivos de su lista usando un bucle.
    """
    bucket_name = "datos-practica2-sd-ivan-pere"
    insultos_totales_chunk = 0

    print(f"📦 [MAP BATCH] Esta Lambda va a procesar {len(lista_archivos)} archivos de golpe: {lista_archivos}")

    for nombre_archivo in lista_archivos:
        # Lectura
        contenido = storage.get_object(bucket=bucket_name, key=nombre_archivo).decode('utf-8')
        texto_censurado, num_insultos = censurar_insultos(contenido)
        
        # Escritura
        nombre_salida = "censurado_" + nombre_archivo
        storage.put_object(bucket=bucket_name, key=nombre_salida, body=texto_censurado.encode('utf-8'))
        
        insultos_totales_chunk += num_insultos

    return insultos_totales_chunk

# =====================================================================
# 3. FASE REDUCE (Intacta)
# =====================================================================
def reduce_total_insults(resultados_mapas):
    print("\n🔄 [REDUCE] Agregando resultados de las Lambdas...")
    return sum(resultados_mapas)

# =====================================================================
# 4. LA OPERACIÓN BATCH DEL EJERCICIO 4
# =====================================================================
def operacion_batch(funcion_map, maxfunc, bucket_name, fexec):
    print(f"[..] Escaneando archivos dentro del bucket '{bucket_name}'...")
    lista_objetos = fexec.storage.list_objects(bucket=bucket_name)

    nombres_archivos = []
    for item in lista_objetos:
        k_name = item['Key'] if isinstance(item, dict) else item.key
        if not k_name.startswith('censurado_'):
            nombres_archivos.append(k_name)

    # Lógica de reparto de "cartas" (archivos) en 'maxfunc' montones (chunks)
    n_chunks = min(maxfunc, len(nombres_archivos))
    chunks = [[] for _ in range(n_chunks)]
    
    for i, archivo in enumerate(nombres_archivos):
        chunks[i % n_chunks].append(archivo)

    print(f"[>] Disparando Operación Batch: {len(nombres_archivos)} archivos repartidos en solo {n_chunks} Lambdas concurrentes.")
    
    # Lithops ahora pasará cada sub-lista (chunk) a una Lambda distinta
    fexec.map_reduce(funcion_map, chunks, reduce_total_insults)
    return fexec.get_result()

# =====================================================================
# ORQUESTADOR
# =====================================================================
if __name__ == "__main__":
    import os
    BUCKET_NAME = "datos-practica2-sd-ivan-pere"
    carpeta_origen_fisica = "./datos_s3_simulado"
    
    # Definimos el límite que nos pide el ejercicio
    MAX_FUNCIONES = 3 

    print("[+] Inicializando ejecutor de Lithops...")
    fexec = lithops.FunctionExecutor(config_file='.lithops_config')

    # --- AÑADIMOS ESTA PARTE PARA SUBIR LOS ARCHIVOS FRESCOS A AWS S3 ---
    print("[*] Subiendo archivos frescos al bucket real de AWS...")
    for f in os.listdir(carpeta_origen_fisica):
        if f.endswith('.txt') and not f.startswith('censurado_'):
            ruta_completa = os.path.join(carpeta_origen_fisica, f)
            with open(ruta_completa, 'r', encoding='utf-8') as archivo_real:
                fexec.storage.put_object(bucket=BUCKET_NAME, key=f, body=archivo_real.read().encode('utf-8'))
    # --------------------------------------------------------------------

    # Ejecutamos nuestra nueva función batch
    total_insultos = operacion_batch(map_filter_insults_batch, MAX_FUNCIONES, BUCKET_NAME, fexec)

    print("\n=====================================================================")
    print("[+] [REPORTE BATCH FINALIZADO - EJERCICIO 4]")
    print(f" Total de insultos censurados: {total_insultos}")
    print("=====================================================================")