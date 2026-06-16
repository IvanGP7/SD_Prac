import json
import pika
import psycopg2
import time

# --- CONFIGURACIÓN ---
EC2_IP = "44.223.19.153" # Cambiar a tu IP Elástica / Pública
DB_CONFIG = {"dbname": "postgres", "user": "postgres", "password": "admin", "host": EC2_IP, "port": "5432"}

def lambda_handler(event, context):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=EC2_IP))
        channel = connection.channel()
        
        # QoS Prefetch: Evita el "trabajador glotón" y permite escalar
        channel.basic_qos(prefetch_count=10)
        queue = channel.queue_declare(queue='ticket_orders', durable=True, passive=True)
        
        if queue.method.message_count == 0:
            connection.close()
            return {"statusCode": 200, "body": "Cola vacía."}

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        procesados = 0

        for method_frame, properties, body in channel.consume('ticket_orders', inactivity_timeout=1):
            if not method_frame:
                break
                
            order = json.loads(body)
            req_id = order['request_id']
            ticket_type = order['type']
            
            # Idempotencia: Verificar si ya se procesó
            cursor.execute("SELECT status FROM processed_requests WHERE request_id = %s", (req_id,))
            if cursor.fetchone():
                channel.basic_ack(method_frame.delivery_tag)
                continue

            # Iniciar transacción y guardar tiempo de inicio exacto en BD
            cursor.execute("INSERT INTO processed_requests (request_id, status, started_at) VALUES (%s, 'PROCESSING', clock_timestamp())", (req_id,))
            
            # Requisito 4: Latencia artificial 100ms
            time.sleep(0.100) 
            
            try:
                if ticket_type == 'UNNUMBERED':
                    # Bloqueo Pesimista (Evita condiciones de carrera)
                    cursor.execute("SELECT available_tickets FROM events WHERE event_id = 1 FOR UPDATE;")
                    if cursor.fetchone()[0] > 0:
                        cursor.execute("UPDATE events SET available_tickets = available_tickets - 1 WHERE event_id = 1;")
                        cursor.execute("UPDATE processed_requests SET status = 'SUCCESS', completed_at = clock_timestamp() WHERE request_id = %s", (req_id,))
                        conn.commit()
                        channel.basic_ack(method_frame.delivery_tag)
                        procesados += 1
                    else:
                        conn.rollback()
                        channel.basic_ack(method_frame.delivery_tag)
                        
                elif ticket_type == 'NUMBERED':
                    seat_num = order['seat_number']
                    # Bloqueo Pesimista sobre un asiento específico
                    cursor.execute("SELECT status FROM seats WHERE event_id = 1 AND seat_number = %s FOR UPDATE;", (seat_num,))
                    if cursor.fetchone()[0] == 'AVAILABLE':
                        cursor.execute("UPDATE seats SET status = 'SOLD' WHERE event_id = 1 AND seat_number = %s;", (seat_num,))
                        cursor.execute("UPDATE processed_requests SET status = 'SUCCESS', completed_at = clock_timestamp() WHERE request_id = %s", (req_id,))
                        conn.commit()
                        channel.basic_ack(method_frame.delivery_tag)
                        procesados += 1
                    else:
                        conn.rollback()
                        channel.basic_ack(method_frame.delivery_tag)
                        
            except Exception as e:
                conn.rollback()
                # Enviar a cola de reintentos (Fault Tolerance: at-least-once)
                channel.basic_nack(method_frame.delivery_tag, requeue=True)

        channel.cancel()
        cursor.close()
        conn.close()
        connection.close()

        return {"statusCode": 200, "body": f"Procesados: {procesados}"}

    except Exception as e:
        print(f"Error crítico: {e}")
        return {"statusCode": 500, "body": str(e)}