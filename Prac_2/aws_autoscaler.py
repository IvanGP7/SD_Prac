import pika
import time
import csv
import boto3
from botocore.exceptions import ClientError

# --- CONFIGURACIÓN ---
RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'ticket_orders'
LAMBDA_FUNCTION_NAME = 'TicketWorkerLambda'

# Parámetros Matemáticos del Escalado
CAPACIDAD_WORKER = 10  # C = mensajes por segundo (Prefetch = 10)
TIEMPO_RESPUESTA_OBJETIVO = 2  # Tr = Segundos

lambda_client = boto3.client('lambda', region_name='us-east-1')

def get_queue_backlog():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        queue = channel.queue_declare(queue=QUEUE_NAME, durable=True, passive=True)
        backlog = queue.method.message_count
        connection.close()
        return backlog
    except Exception as e:
        print(f"Error al conectar con RabbitMQ: {e}")
        return 0

def update_lambda_concurrency(desired_concurrency):
    try:
        if desired_concurrency > 0:
            lambda_client.put_function_concurrency(
                FunctionName=LAMBDA_FUNCTION_NAME,
                ReservedConcurrentExecutions=desired_concurrency
            )
        else:
            lambda_client.delete_function_concurrency(
                FunctionName=LAMBDA_FUNCTION_NAME
            )
    except ClientError as e:
        print(f"Error ajustando concurrencia: {e}")

def main():
    print("🚀 AWS Autoescalador Iniciado. Monitorizando RabbitMQ y controlando Lambda...")
    
    # Creamos un CSV nuevo por cada ejecución
    csv_filename = f"scaling_metrics_{int(time.time())}.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time_Seconds', 'Backlog', 'Active_Workers'])
        
        start_time = time.time()
        
        while True:
            current_time = int(time.time() - start_time)
            backlog = get_queue_backlog()
            
            # FÓRMULA MATEMÁTICA DE ESCALADO: N = B / (Tr * C)
            desired_workers = (backlog // (TIEMPO_RESPUESTA_OBJETIVO * CAPACIDAD_WORKER)) + 1
            
            if backlog == 0:
                desired_workers = 0
            
            # Límite de seguridad
            desired_workers = min(desired_workers, 15)
            
            update_lambda_concurrency(desired_workers)
            writer.writerow([current_time, backlog, desired_workers])
            file.flush() # Guardar a disco inmediatamente
            
            if backlog > 0:
                print(f"[SCALE] Backlog: {backlog} | Disparando {desired_workers} Lambdas concurrentes en AWS...")
            else:
                print(f"[IDLE] Backlog: 0. Esperando tráfico...")
                
            time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")