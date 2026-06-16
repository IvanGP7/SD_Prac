import pika
import json
import uuid
import time
import random

def send_traffic(scenario_choice):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='ticket_orders', durable=True)

    # Definición de fases elásticas Z(t) - (Mensajes por fase, Mensajes por segundo)
    fases = [
        ("Low load phase", 50, 5),
        ("Gradual ramp-up", 200, 20),
        ("Sudden spikes", 500, 100),
        ("Sustained high load", 1500, 50),
        ("Cool-down phase", 50, 5)
    ]
    
    total_injected = 0
    
    for nombre_fase, total_mensajes, rate in fases:
        print(f"--> Fase: {nombre_fase} | {rate} req/s")
        sleep_time = 1.0 / rate
        
        for _ in range(total_mensajes):
            req_id = str(uuid.uuid4())
            
            if scenario_choice == '1': # Unnumbered
                order = {"request_id": req_id, "type": "UNNUMBERED"}
            elif scenario_choice == '2': # Numbered - Uniform
                order = {"request_id": req_id, "type": "NUMBERED", "seat_number": random.randint(1, 100000)}
            elif scenario_choice == '3': # Numbered - Hotspot (80% a 5% de asientos)
                if random.random() < 0.80:
                    seat = random.randint(1, 5000) # El 5% caliente
                else:
                    seat = random.randint(5001, 100000)
                order = {"request_id": req_id, "type": "NUMBERED", "seat_number": seat}

            channel.basic_publish(
                exchange='',
                routing_key='ticket_orders',
                body=json.dumps(order),
                properties=pika.BasicProperties(delivery_mode=2) # Persistente
            )
            total_injected += 1
            time.sleep(sleep_time)

    print(f"[✓] Prueba finalizada. Total inyectados: {total_injected}")
    connection.close()

if __name__ == "__main__":
    print("=== TAREA 2: SIMULADOR DE ESCENARIOS Z(t) ===")
    print("1. [Unnumbered] Entradas sin numerar")
    print("2. [Numbered]   Uniform Load (Sin contención fuerte)")
    print("3. [Numbered]   Hotspot Load (Alta contención: 80% van a 5% asientos)")
    choice = input("Elige el escenario (1, 2 o 3): ")
    send_traffic(choice)