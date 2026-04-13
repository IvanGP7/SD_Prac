import pika
import json
from Worker import TicketWorker

worker_core = TicketWorker(host='localhost')

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declaramos las colas de tareas y control
channel.queue_declare(queue='ticket_requests', durable=True)
channel.queue_declare(queue='control_queue', durable=True)

def task_callback(ch, method, body):
    task = json.loads(body)
    if task["type"] == "unnumbered":
        result = worker_core.buy_unnumbered(task["client_id"], task["request_id"])
    else:
        result = worker_core.buy_numbered(task["client_id"], task["seat_id"], task["request_id"])
    
    worker_core.r.rpush("benchmark_results", json.dumps(result))
    print(f" [v] Procesado: {result['status']} para {task['client_id']}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def control_callback(ch, method, body):
    command = body.decode()
    if command == "RESET":
        print("\n[!] RECIBIDO COMANDO DE REINICIO [!]")
        worker_core.reset_system()
        # Opcional: También podrías limpiar la cola de resultados si quieres
        worker_core.r.delete("benchmark_results")
        print(" -> Sistema limpio y listo para el siguiente benchmark.\n")
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Configuramos ambos consumidores en el mismo script
channel.basic_qos(prefetch_count=1)

channel.basic_consume(queue='ticket_requests', on_message_callback=task_callback)
channel.basic_consume(queue='control_queue', on_message_callback=control_callback)

print(" [*] Worker escuchando TAREAS y CONTROL. Ctrl+C para salir.")
channel.start_consuming()