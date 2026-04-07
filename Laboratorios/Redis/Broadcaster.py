import redis
import time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

print("Broadcaster activo...")

# Para este ejercicio, leeremos el último de la lista cada pocos segundos
last_index = 0
while True:
    insultos = r.lrange("INSULTS", last_index, -1)
    for i in insultos:
        r.publish("canal_insultos", i)
        print(f"Publicado en PubSub: {i}")
        last_index += 1
    time.sleep(2)