# map_reduce_lithops.py
import os
import sys
import lithops

# Lista de insultos
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
# FASE MAP: La versión más pura (Recibe un String y el Storage)
# =====================================================================
def map_filter_insults(nombre_archivo, storage):
    """
    Lithops inyectará el String con el nombre de archivo en 'nombre_archivo'
    y el cliente de almacenamiento en 'storage'. ¡Cero diccionarios, cero errores!
    """
    # El bucket lo declaramos aquí dentro (es el mismo para todos)
    bucket_name = "datos-practica2-sd-ivan-pere"
    
    print(f"[MAP] Procesando archivo: {nombre_archivo}")
    
    # Lectura
    contenido = storage.get_object(bucket=bucket_name, key=nombre_archivo).decode('utf-8')
        
    texto_censurado, num_insultos = censurar_insultos(contenido)
    
    # Escritura
    nombre_salida = "censurado_" + nombre_archivo
    storage.put_object(bucket=bucket_name, key=nombre_salida, body=texto_censurado.encode('utf-8'))
        
    print(f"[MAP] Guardado: {nombre_salida} | Insultos: {num_insultos}")
    
    return num_insultos

# =====================================================================
# FASE REDUCE
# =====================================================================
def reduce_total_insults(resultados_mapas):
    print("\n[REDUCE] Iniciando agregación global...")
    return sum(resultados_mapas)

# =====================================================================
# ORQUESTADOR
# =====================================================================
if __name__ == "__main__":
    BUCKET_NAME = "datos-practica2-sd-ivan-pere"
    carpeta_origen_fisica = "./datos_s3_simulado"
    
    if not os.path.exists(carpeta_origen_fisica):
        print(f"[!] Error: Asegúrate de crear la carpeta '{carpeta_origen_fisica}'")
        exit()

    print("[+] Inicializando ejecutor de Lithops...")
    fexec = lithops.FunctionExecutor(config_file='.lithops_config')
    
    print("[*] Cargando archivos en el almacenamiento virtual...")
    for f in os.listdir(carpeta_origen_fisica):
        if f.endswith('.txt') and not f.startswith('censurado_'):
            ruta_completa = os.path.join(carpeta_origen_fisica, f)
            with open(ruta_completa, 'r', encoding='utf-8') as archivo_real:
                fexec.storage.put_object(bucket=BUCKET_NAME, key=f, body=archivo_real.read().encode('utf-8'))

    print(f"[0] Escaneando archivos dentro del bucket '{BUCKET_NAME}'...")
    lista_objetos = fexec.storage.list_objects(bucket=BUCKET_NAME)
    
    # CREAMOS UNA SIMPLE LISTA DE STRINGS
    nombres_archivos = []
    for item in lista_objetos:
        # Extraemos solo el nombre en formato texto
        k_name = item['Key'] if isinstance(item, dict) else item.key
        if not k_name.startswith('censurado_'):
            nombres_archivos.append(k_name)
            
    print(f"[>] Disparando MapReduce sobre {len(nombres_archivos)} archivos en paralelo...")
    
    # Invocamos pasándole simplemente la lista de textos: ['archivo_1.txt', 'archivo_2.txt', ...]
    fexec.map_reduce(map_filter_insults, nombres_archivos, reduce_total_insults)
    
    print("[><] Sincronizando ejecuciones...")
    total_insultos = fexec.get_result()
    
    print("\n=====================================================================")
    print("[+] [REPORTE MAPREDUCE BATCH FINALIZADO]")
    print(f"  Total de insultos censurados en toda la colección: {total_insultos}")
    print("=====================================================================")