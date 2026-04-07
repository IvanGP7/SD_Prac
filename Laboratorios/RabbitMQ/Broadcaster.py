import pika
import redis
import time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declaramos un Exchange de tipo 'fanout' (Difusión total)
channel.exchange_declare(exchange='logs_insultos', exchange_type='fanout')

print("InsultBroadcaster leyendo de Redis y difundiendo...")

last_index = 0
while True:
    insultos = r.lrange("INSULTS", last_index, -1)
    for i in insultos:
        channel.basic_publish(exchange='logs_insultos', routing_key='', body=i)
        print(f" [P] Difundido vía Rabbit Exchange: {i}")
        last_index += 1
    time.sleep(2)