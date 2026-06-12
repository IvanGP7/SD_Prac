import redis
import json
import time
from config import REDIS_HOST, REDIS_PORT

# Lista base de insultos para la censura
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

def lambda_handler(event, context_id):
    """
    Simulación de la ejecución de una AWS Lambda conectada al backend en la nube.
    """
    textos_a_procesar = event.get('mensajes', [])
    print(f"   [Lambda-{context_id}] [->] Iniciada. Procesando lote de {len(textos_a_procesar)} mensajes...")

    # Conexión directa a la base de datos Redis en tu máquina EC2 de AWS
    r_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

    total_insultos_lote = 0
    resultados_procesados = []

    for msg in textos_a_procesar:
        texto_limpio, num_insultos = censurar_insultos(msg)
        total_insultos_lote += num_insultos
        resultados_procesados.append(texto_limpio)
        time.sleep(0.05) # Simulación de una pequeña carga de cómputo por mensaje

    # --- ESCRITURA ATÓMICA EN LA NUBE (REDIS) ---
    pipeline = r_db.pipeline()
    pipeline.incrby("total_insultos_censurados", total_insultos_lote)
    for res in resultados_procesados:
        pipeline.rpush("historico_censuras", json.dumps({"texto": res, "timestamp": time.time()}))
    pipeline.execute()

    print(f"   [Lambda-{context_id}] [+] Procesamiento elástico completado. Insultos: {total_insultos_lote}")
    return {"statusCode": 200, "processed": len(resultados_procesados)}