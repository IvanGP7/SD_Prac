import pika
import sys
import json

def run_indirect_producer(file_path):
    # Conexión a RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='ticket_requests', durable=True)

    print(f"Enviando benchmark a RabbitMQ: {file_path}")

    with open(file_path, 'r') as f:
        for line in f:
            parts = line.split()
            if not parts or parts[0] != "BUY": continue
            
            # Creamos un diccionario con la tarea
            task = {
                "type": "unnumbered" if len(parts) == 3 else "numbered",
                "client_id": parts[1],
                "request_id": parts[-1],
                "seat_id": parts[2] if len(parts) == 4 else None
            }

            # Publicamos en la cola
            channel.basic_publish(
                exchange='',
                routing_key='ticket_requests',
                body=json.dumps(task),
                properties=pika.BasicProperties(delivery_mode=2) # Mensaje persistente
            )

    print("Todas las peticiones han sido encoladas.")
    connection.close()

if __name__ == "__main__":
    run_indirect_producer(sys.argv[1])