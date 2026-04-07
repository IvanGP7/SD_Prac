import pika
import time
import random

# Configuración de RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declaramos la cola
channel.queue_declare(queue='insult_queue')

insultos_base = ["Zopenco", "Mentecato", "Mastuerzo", "Energumeno"]

print("RabbitMQ InsultProducer iniciado...")

while True:
    insulto = random.choice(insultos_base)
    channel.basic_publish(exchange='', routing_key='insult_queue', body=insulto)
    print(f" [x] Enviado a RabbitMQ: {insulto}")
    time.sleep(5)