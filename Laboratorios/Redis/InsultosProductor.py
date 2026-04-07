import redis
import time
import random

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
insultos_base = ["Zopenco", "Mentecato", "Mastuerzo", "Energumeno", "Papanatas"]

print("Productor de insultos iniciado...")

while True:
    insulto = random.choice(insultos_base)
    # Metemos el insulto en la "cola" (Lado izquierdo de la lista)
    r.lpush("queue:insults", insulto)
    print(f"Enviado a la cola: {insulto}")
    time.sleep(5)