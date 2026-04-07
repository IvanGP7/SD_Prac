import pika
import json
from Worker import TicketWorker

# Instanciamos la lógica que ya probaste
worker_core = TicketWorker(host='localhost')

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='ticket_requests', durable=True)

# Importante: Solo dar 1 tarea a la vez a cada worker (Fair Dispatch)
channel.basic_qos(prefetch_count=1)

def callback(ch, method, properties, body):
    task = json.loads(body)
    
    if task["type"] == "unnumbered":
        result = worker_core.buy_unnumbered(task["client_id"], task["request_id"])
    else:
        result = worker_core.buy_numbered(task["client_id"], task["seat_id"], task["request_id"])
    
    # En este modelo, el resultado se suele guardar en una lista de Redis 
    # para que luego el cliente pueda consultar si su compra fue exitosa.
    worker_core.r.rpush("benchmark_results", json.dumps(result))
    
    print(f" [v] Procesado: {result['status']} para {task['client_id']}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

print(" [*] Worker esperando tareas. Ctrl+C para salir.")
channel.basic_consume(queue='ticket_requests', on_message_callback=callback)
channel.start_consuming()