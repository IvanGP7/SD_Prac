import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe("canal_insultos")

print("Receptor esperando mensajes del Broadcaster...")

for mensaje in pubsub.listen():
    if mensaje['type'] == 'message':
        print(f"Mensaje recibido por PubSub: {mensaje['data']}")