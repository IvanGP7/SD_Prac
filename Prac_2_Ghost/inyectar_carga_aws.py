# inyectar_carga_aws.py
import pika
import random
import time
from config import RABBITMQ_HOST, RABBITMQ_PORT, QUEUE_NAME

# Batería de frases de prueba (mezclando insultos para estresar el filtro)
frases_ejemplo = [
    "Este es un comentario completamente constructivo y educado para el foro.",
    "Menudo tonto estás hecho, de verdad que eres un pesado de cuidado.",
    "Hola a todos, espero que tengáis un excelente día de trabajo.",
    "No te aguanto más porque eres un auténtico idiota y un bobo.",
    "Por favor, mantengamos el respeto en el canal distribuidor.",
    "Vaya imbecil, siempre con las mismas tonterías de siempre."
]

print(f"[*] Conectando al broker RabbitMQ en AWS: {RABBITMQ_HOST}")

# Establecer conexión remota con la EC2
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
)
channel = connection.channel()

# Nos aseguramos de que la cola exista antes de publicar
channel.queue_declare(queue=QUEUE_NAME, durable=True)

VOLUMEN_PETICIONES = 150
print(f"[->] Inyectando ráfaga masiva de {VOLUMEN_PETICIONES} mensajes en la cola remota...")

for i in range(VOLUMEN_PETICIONES):
    # Seleccionamos una frase aleatoria y le metemos un ID único al final
    msg_body = random.choice(frases_ejemplo) + f" (Mensaje ID: {i})"

    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=msg_body,
        properties=pika.BasicProperties(
            delivery_mode=2 # Mensaje persistente (guarda en disco por si acaso)
        )
    )

print("[+] Inyección completada con éxito.")
print("[*] Mira la pantalla de tu monitor 'stream_auto_scaling.py' para ver la elasticidad en acción.")

connection.close()