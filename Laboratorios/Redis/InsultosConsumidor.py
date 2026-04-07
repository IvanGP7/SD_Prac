import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

print("Consumidor esperando insultos...")

while True:
    # BRPOP devuelve (nombre_cola, valor). Timeout 0 = esperar siempre.
    _, insulto = r.brpop("queue:insults", timeout=0)
    
    # Verificar si es nuevo en la lista final 'INSULTS'
    # SISMEMBER es para SETS (conjuntos), pero el ejercicio pide LISTA.
    # Usamos LPOS (disponible en Redis moderno) o revisamos la lista:
    existentes = r.lrange("INSULTS", 0, -1)
    
    if insulto not in existentes:
        r.rpush("INSULTS", insulto)
        print(f"Nuevo insulto guardado en INSULTS: {insulto}")
    else:
        print(f"Insulto ignorado (duplicado): {insulto}")