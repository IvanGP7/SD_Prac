import pika
import json
import time
import sys
import redis

def send_reset_signal(ip_servidor):
    connection = pika.BlockingConnection(pika.ConnectionParameters(ip_servidor))
    channel = connection.channel()
    channel.queue_declare(queue='control_queue', durable=True)
    
    channel.basic_publish(
        exchange='',
        routing_key='control_queue',
        body='RESET',
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

def run_indirect_benchmark(file_path, ip_servidor):
    # 1. Conexión a Redis para limpiar y monitorear resultados
    r_db = redis.Redis(host=ip_servidor, port=6379, decode_responses=True)
    r_db.delete("benchmark_results") # Limpiar pruebas anteriores

    # 2. Conexión a RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(ip_servidor))
    channel = connection.channel()
    channel.queue_declare(queue='ticket_requests', durable=True)

    # Contadores locales para el envío
    total_requests = 0
    
    # print(f"Iniciando benchmark INDIRECTO: {file_path}")
    start_time = time.time()

    # 3. FASE DE ENVÍO (Productor)
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.split()
            if not parts or parts[0] != "BUY": continue
            
            total_requests += 1
            task = {
                "type": "unnumbered" if len(parts) == 3 else "numbered",
                "client_id": parts[1],
                "request_id": parts[-1],
                "seat_id": parts[2] if len(parts) == 4 else None
            }

            channel.basic_publish(
                exchange='',
                routing_key='ticket_requests',
                body=json.dumps(task),
                properties=pika.BasicProperties(delivery_mode=2)
            )

    # print(f" [x] {total_requests} peticiones encoladas. Esperando a los workers...")

    # 4. FASE DE ESPERA (Monitorización)
    # El benchmark no termina hasta que el último worker procesa su tarea
    while True:
        processed_count = r_db.llen("benchmark_results")
        if processed_count >= total_requests:
            break
        time.sleep(0.1) # Evitar saturar la CPU con el bucle

    end_time = time.time()
    total_time = end_time - start_time

    # 5. RECOLECCIÓN DE RESULTADOS (Desde Redis)
    results = r_db.lrange("benchmark_results", 0, -1)
    success_count = sum(1 for res in results if json.loads(res)["status"] == "SUCCESS")
    failure_count = total_requests - success_count

    # Reporte de métricas (Idéntico al directo)
    print("\n--- RESULTADOS DEL BENCHMARK (INDIRECTO/RABBITMQ) ---")
    print(f"Archivo: {file_path}")
    print(f"Tiempo total (incluyendo proceso): {total_time:.2f} segundos")
    print(f"Throughput Global: {total_requests / total_time:.2f} ops/sec")
    print(f"Éxitos: {success_count} | Fallos: {failure_count}")
    print("----------------------------------------------------\n")

    
    connection.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python client_benchmark_indirect.py <ruta_del_archivo.txt> <ip_del_servidor>")
    else:
        run_indirect_benchmark(sys.argv[1], sys.argv[2])
        send_reset_signal(sys.argv[2])