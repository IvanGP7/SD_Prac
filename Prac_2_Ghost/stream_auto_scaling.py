import pika
import threading
import time
import uuid
from config import RABBITMQ_HOST, RABBITMQ_PORT, QUEUE_NAME
from worker_lambda import lambda_handler

def stream_operation(function, maxfunc, queue_name):
    """
    Algoritmo de Auto-escalado que monitoriza la cola remota en AWS EC2.
    """
    print(f"[+] Conectando al monitor de auto-escalado en AWS: {RABBITMQ_HOST}")
    print(f"[-] Cola objetivo: '{queue_name}' | Límite máximo (maxfunc): {maxfunc}\n")

    # Conexión remota al RabbitMQ de la EC2
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
    channel = connection.channel()

    # Asegurar que la cola existe en el servidor remoto
    channel.queue_declare(queue=queue_name, durable=True)

    hilos_activos = []

    try:
        while True:
            # 1. Limpiar del registro las Lambdas que ya terminaron su trabajo
            hilos_activos = [h for h in hilos_activos if h.is_alive()]
            num_workers_actuales = len(hilos_activos)

            # 2. Consultar el estado de carga de la cola en AWS de forma pasiva
            queue_info = channel.queue_declare(queue=queue_name, passive=True)
            num_mensajes = queue_info.method.message_count

            print(f"[Monitor] Mensajes en Cola AWS: {num_mensajes} | Instancias Lambdas activas: {num_workers_actuales}/{maxfunc}")

            # 3. FÓRMULA MATEMÁTICA DE AUTO-ESCALADO
            # Regla: 1 Lambda por cada 20 mensajes pendientes.
            if num_mensajes > 0:
                workers_teoricos = (num_mensajes // 20) + 1
                workers_objetivo = min(maxfunc, max(1, workers_teoricos))
            else:
                workers_objetivo = 0

            # 4. CONTROL DE CONCURRENCIA (SCALE UP)
            if num_workers_actuales < workers_objetivo:
                lambdas_a_lanzar = workers_objetivo - num_workers_actuales
                print(f"[Scale UP] Detectada sobrecarga. Instanciando {lambdas_a_lanzar} nuevo(s) worker(s)...")

                for _ in range(lambdas_a_lanzar):
                    # Extraer un lote de hasta 20 mensajes de la cola remota para este trabajador
                    lote_mensajes = []
                    for _ in range(20):
                        method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)
                        if method_frame:
                            lote_mensajes.append(body.decode('utf-8'))
                        else:
                            break

                    if lote_mensajes:
                        event_payload = {"mensajes": lote_mensajes}
                        lambda_id = str(uuid.uuid4())[:8]

                        # Lanzamos la ejecución simulando la llamada asíncrona de AWS Lambda
                        t = threading.Thread(target=function, args=(event_payload, lambda_id))
                        hilos_activos.append(t)
                        t.start()

            # Comprobación de estado cada 3 segundos
            time.sleep(3)

    except KeyboardInterrupt:
        print("\n[!] Deteniendo el monitor de auto-escalado.")
    finally:
        connection.close()

if __name__ == "__main__":
    # Ejecutamos la primitiva pasando la lambda, el límite de concurrencia y la cola
    stream_operation(lambda_handler, maxfunc=5, queue_name=QUEUE_NAME)