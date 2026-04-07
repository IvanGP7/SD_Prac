import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declaramos el mismo exchange
channel.exchange_declare(exchange='logs_insultos', exchange_type='fanout')

# Creamos una cola aleatoria y exclusiva para este receptor
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# Unimos (Binding) nuestra cola temporal al exchange
channel.queue_bind(exchange='logs_insultos', queue=queue_name)

def callback(ch, method, properties, body):
    print(f" Receptor recibió: {body.decode()}")

print("InsultReceiver esperando difusión. Pulsa Ctrl+C para salir.")
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()