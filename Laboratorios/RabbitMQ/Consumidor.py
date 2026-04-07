import pika
import redis

# Conexión Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Conexión RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='insult_queue')

def callback(ch, method, properties, body):
    insulto = body.decode()
    # Verificar en Redis si es nuevo
    existentes = r.lrange("INSULTS", 0, -1)
    if insulto not in existentes:
        r.rpush("INSULTS", insulto)
        print(f" [v] Nuevo insulto guardado en REDIS: {insulto}")
    else:
        print(f" [!] Duplicado detectado: {insulto}")

print("InsultConsumer esperando mensajes de RabbitMQ...")
channel.basic_consume(queue='insult_queue', on_message_callback=callback, auto_ack=True)
channel.start_consuming()