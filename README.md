# SD_Prac
## Guía de Ejecución Distribuida (Dos Máquinas)

Esta sección describe cómo ejecutar los benchmarks utilizando dos máquinas físicas en red local (p. ej., Torre como Servidor y Portátil como Cliente) para validar la escalabilidad horizontal y el comportamiento del sistema.

### Requisitos Previos
1. **Identificar la IP del Servidor:** En la máquina Servidor (Torre), abre una terminal y ejecuta `ipconfig`. Busca la dirección IPv4 (ej. `192.168.1.50`).
2. **Conectividad:** Ambas máquinas deben estar en la misma red local. Asegúrate de que el Firewall de la máquina servidor permita los puertos:
   * **6379** (Redis)
   * **5672** (RabbitMQ)
   * **9090** (Pyro Name Server)
3. **Servicios:** Asegúrate de que Docker (Redis y RabbitMQ) esté corriendo en el Servidor.

---

### Fase 1: Configuración del Servidor (Máquina A - Torre)

Ejecuta los siguientes comandos en terminales separadas dentro de la máquina servidor:

#### 1. Iniciar el Name Server de Pyro4
```bash
python -m Pyro4.naming -n [IP_SERVIDOR]
```
2. Lanzar Nodos de Arquitectura Directa (Pyro4)
Lanza tantos nodos como desees para probar el balanceo:

```Bash
python .\Prac_1\src\Server_direct.py [IP_SERVIDOR] nodo1
python .\Prac_1\src\Server_direct.py [IP_SERVIDOR] nodo2
```

3. Lanzar Workers de Arquitectura Indirecta (RabbitMQ)
```Bash
python .\Prac_1\src\Server_indirect.py
```

### Fase 2: Ejecución del Benchmark (Máquina B - Portátil)
Desde la máquina cliente, lanza las pruebas apuntando a la IP de la torre:

Comentario: Para recolectar los datos que alimentarán las gráficas, se recomienda redirigir la salida estándar de la consola a un archivo .txt dentro de la carpeta Resultados utilizando el operador >> de PowerShell.

1. Benchmark Arquitectura Directa (Balanceado)
```Bash
python .\Prac_1\src\client_direct_benchmark.py .\Prac_1\Benchmarks\benchmark_unnumbered_20000.txt [IP_SERVIDOR] >> .\Prac_1\Resultados\tiempos_1_nodo.txt
```
2. Benchmark Arquitectura Indirecta (RabbitMQ)
```Bash
python .\Prac_1\src\client_indirect_benchmark.py .\Prac_1\Benchmarks\benchmark_numbered_60000.txt [IP_SERVIDOR] >> .\Prac_1\Resultados\tiempos_1_nodo.txt
```
3. Generación Automática de Gráficas
```Bash
python .\Prac_1\src\analizar_resultados.py .\Prac_1\Resultados\
```
Análisis de Resultados Esperados
Escalabilidad Pyro4: El rendimiento total (throughput) se mantendrá prácticamente plano e invariable (en torno a las ~150 ops/sec) sin importar cuántos nodos añadas. Esto demuestra que en arquitecturas síncronas el cliente bloqueante y la latencia RTT de la red actúan como cuello de botella.

Escalabilidad RabbitMQ: l añadir más workers distribuidos, la capacidad de procesamiento del sistema aumenta de forma drástica (alcanzando picos de +2600 ops/sec). El cliente se libera de inmediato mediante un esquema fire-and-forget y delega la concurrencia a la cola distribuidora.

Consistencia: En el test de asientos numerados (60k), notarás una ligera penalización de rendimiento al llegar a los 8 workers distribuidos en comparación con los 6 workers. Esto modela visualmente el impacto de la contención sobre la base de datos (Redis), donde la persistencia y la gestión de bloqueos simultáneos de recursos compartidos definen el límite de escalabilidad horizontal del sistema.

# Scalable and Elastic Ticket Service (AWS)

Este documento contiene la guia de despliegue, la arquitectura y el codigo fuente completo de un sistema distribuido, escalable y tolerante a fallos para la venta de entradas utilizando servicios gestionados de AWS.

## 1. Arquitectura del Sistema

El sistema sigue una arquitectura asincrona basada en el patron Productor-Consumidor para garantizar el procesamiento exacto y la tolerancia a picos de carga:
* **Queue/Broker:** RabbitMQ (Desplegado en EC2) para suavizado de carga (*Load smoothing*) y desacoplamiento.
* **Stateless Workers:** AWS Lambda (Python 3.10) para procesamiento elastico bajo demanda.
* **Persistent Storage:** PostgreSQL (Desplegado en EC2) con control de concurrencia pesimista (`FOR UPDATE`) para evitar la sobreventa.
* **Auto-scaler:** Script Python personalizado que aplica escalado dinamico basado en el Backlog de la cola utilizando la formula: `N = B / (Tr * C)`.

---

## 2. Prerrequisitos

1. Instancia AWS EC2 (Amazon Linux 2023 o similar) con IP Elastica.
2. Docker instalado en la instancia EC2.
3. Python 3.9+ instalado localmente y en EC2.
4. Rol IAM de AWS con permisos de invocacion y actualizacion de concurrencia para AWS Lambda.
5. AWS CLI configurado en la instancia EC2.

---

## 3. Guia de Despliegue (Deployment Guide)

### 3.1. Infraestructura Base (EC2)
Conectate a tu instancia EC2 por SSH y ejecuta los siguientes comandos para levantar la base de datos y el broker de mensajeria:

```bash
# Iniciar RabbitMQ
sudo docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Iniciar PostgreSQL
sudo docker run -d --name postgres -e POSTGRES_PASSWORD=admin -p 5432:5432 postgres
```

### 3.2. Inicializacion de la Base de Datos
Ejecuta los siguientes comandos para crear el esquema de base de datos y los 100.000 tickets disponibles:

```bash
sudo docker exec -it postgres psql -U postgres

# Dentro de la consola SQL:
CREATE TABLE events (event_id INT PRIMARY KEY, available_tickets INT);
INSERT INTO events VALUES (1, 100000);

CREATE TABLE seats (event_id INT, seat_number INT, status VARCHAR(20), PRIMARY KEY (event_id, seat_number));
INSERT INTO seats (event_id, seat_number, status) SELECT 1, generate_series(1, 100000), 'AVAILABLE';

CREATE TABLE processed_requests (request_id VARCHAR(255) PRIMARY KEY, status VARCHAR(20), started_at TIMESTAMP, completed_at TIMESTAMP);
```

### 3.3. Entorno de Control y Dependencias
Instala las dependencias en tu EC2 para ejecutar los scripts de orquestacion:

```bash
pip3 install pika boto3 psycopg2-binary pandas matplotlib
```

---

## 4. Codigo Fuente (Source Code)

A continuacion se detallan los 5 scripts principales que componen el sistema. 

### A. Worker Elastico (AWS Lambda)
**Archivo:** `lambda_worker.py`
**Proposito:** Procesar mensajes asincronos, aplicar latencia artificial de 100ms, garantizar idempotencia y prevenir sobreventa con bloqueos a nivel de fila (`FOR UPDATE`).

```python
import json
import pika
import psycopg2
import time

EC2_IP = "TU_IP_ELASTICA"
DB_CONFIG = {"dbname": "postgres", "user": "postgres", "password": "admin", "host": EC2_IP, "port": "5432"}

def lambda_handler(event, context):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=EC2_IP))
        channel = connection.channel()
        channel.basic_qos(prefetch_count=10)
        queue = channel.queue_declare(queue='ticket_orders', durable=True, passive=True)
        
        if queue.method.message_count == 0:
            connection.close()
            return {"statusCode": 200, "body": "Cola vacia."}

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        procesados = 0

        for method_frame, properties, body in channel.consume('ticket_orders', inactivity_timeout=1):
            if not method_frame:
                break
                
            order = json.loads(body)
            req_id = order['request_id']
            ticket_type = order['type']
            
            cursor.execute("SELECT status FROM processed_requests WHERE request_id = %s", (req_id,))
            if cursor.fetchone():
                channel.basic_ack(method_frame.delivery_tag)
                continue

            cursor.execute("INSERT INTO processed_requests (request_id, status, started_at) VALUES (%s, 'PROCESSING', clock_timestamp())", (req_id,))
            time.sleep(0.100) 
            
            try:
                if ticket_type == 'UNNUMBERED':
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
                channel.basic_nack(method_frame.delivery_tag, requeue=True)

        channel.cancel()
        cursor.close()
        conn.close()
        connection.close()
        return {"statusCode": 200, "body": f"Procesados: {procesados}"}

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
```

### B. Autoescalador Dinamico
**Archivo:** `aws_autoscaler.py`
**Proposito:** Monitorizar RabbitMQ y escalar AWS Lambda concurrentemente basandose en la ecuacion de rendimiento.

```python
import pika
import time
import csv
import boto3
from botocore.exceptions import ClientError

RABBITMQ_HOST = 'localhost'
QUEUE_NAME = 'ticket_orders'
LAMBDA_FUNCTION_NAME = 'TicketWorkerLambda'

CAPACIDAD_WORKER = 10
TIEMPO_RESPUESTA_OBJETIVO = 2

lambda_client = boto3.client('lambda', region_name='us-east-1')

def get_queue_backlog():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        queue = channel.queue_declare(queue=QUEUE_NAME, durable=True, passive=True)
        backlog = queue.method.message_count
        connection.close()
        return backlog
    except:
        return 0

def update_lambda_concurrency(desired_concurrency):
    try:
        if desired_concurrency > 0:
            lambda_client.put_function_concurrency(FunctionName=LAMBDA_FUNCTION_NAME, ReservedConcurrentExecutions=desired_concurrency)
        else:
            lambda_client.delete_function_concurrency(FunctionName=LAMBDA_FUNCTION_NAME)
    except ClientError as e:
        print(f"Error ajustando concurrencia: {e}")

def main():
    csv_filename = f"scaling_metrics_{int(time.time())}.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time_Seconds', 'Backlog', 'Active_Workers'])
        start_time = time.time()
        
        while True:
            current_time = int(time.time() - start_time)
            backlog = get_queue_backlog()
            desired_workers = (backlog // (TIEMPO_RESPUESTA_OBJETIVO * CAPACIDAD_WORKER)) + 1
            if backlog == 0: desired_workers = 0
            desired_workers = min(desired_workers, 15)
            
            update_lambda_concurrency(desired_workers)
            writer.writerow([current_time, backlog, desired_workers])
            file.flush()
            time.sleep(2)

if __name__ == "__main__":
    main()
```

### C. Simulador de Carga Z(t)
**Archivo:** `producer.py`
**Proposito:** Inyectar perfiles de carga (Uniform y Hotspot) y simular fases de elasticidad.

```python
import pika
import json
import uuid
import time
import random

def send_traffic(scenario_choice):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='ticket_orders', durable=True)

    fases = [
        ("Low load phase", 50, 5),
        ("Gradual ramp-up", 200, 20),
        ("Sudden spikes", 500, 100),
        ("Sustained high load", 1500, 50),
        ("Cool-down phase", 50, 5)
    ]
    
    for nombre_fase, total_mensajes, rate in fases:
        sleep_time = 1.0 / rate
        for _ in range(total_mensajes):
            req_id = str(uuid.uuid4())
            if scenario_choice == '1':
                order = {"request_id": req_id, "type": "UNNUMBERED"}
            elif scenario_choice == '2':
                order = {"request_id": req_id, "type": "NUMBERED", "seat_number": random.randint(1, 100000)}
            elif scenario_choice == '3':
                seat = random.randint(1, 5000) if random.random() < 0.80 else random.randint(5001, 100000)
                order = {"request_id": req_id, "type": "NUMBERED", "seat_number": seat}

            channel.basic_publish(exchange='', routing_key='ticket_orders', body=json.dumps(order), properties=pika.BasicProperties(delivery_mode=2))
            time.sleep(sleep_time)
    connection.close()

if __name__ == "__main__":
    choice = input("Elige el escenario (1 Unnumbered, 2 Uniform, 3 Hotspot): ")
    send_traffic(choice)
```

### D. Extractor Server-Side Metrics
**Archivo:** `master_csv.py`
**Proposito:** Combinar datos de autoescalado con latencia real end-to-end extraida nativamente desde PostgreSQL.

```python
import psycopg2
import csv
import glob
import os

DB_CONFIG = {"dbname": "postgres", "user": "postgres", "password": "admin", "host": "localhost", "port": "5432"}

try:
    autoscaler_data = {}
    csv_files = glob.glob("scaling_metrics_*.csv")
    latest_csv = max(csv_files, key=os.path.getctime)
    with open(latest_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            autoscaler_data[int(row['Time_Seconds'])] = {'Backlog': row['Backlog'], 'Workers': row['Active_Workers']}
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        WITH start_time AS (SELECT MIN(started_at) as t0 FROM processed_requests)
        SELECT 
            FLOOR(EXTRACT(EPOCH FROM (completed_at - t0)))::int AS time_sec,
            COUNT(*) as throughput,
            COALESCE(percentile_cont(0.50) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))) * 1000, 0) AS p50_ms,
            COALESCE(percentile_cont(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))) * 1000, 0) AS p95_ms,
            COALESCE(percentile_cont(0.99) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at))) * 1000, 0) AS p99_ms
        FROM processed_requests, start_time
        WHERE status = 'SUCCESS' GROUP BY time_sec ORDER BY time_sec;
    """)
    db_data = cursor.fetchall()
    
    with open('FINAL_DATA_SCENARIO.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time_Seconds', 'Backlog', 'Active_Workers', 'Throughput_Req_Sec', 'Latency_p50_ms', 'Latency_p95_ms', 'Latency_p99_ms'])
        max_time = max(max(autoscaler_data.keys(), default=0), max([row[0] for row in db_data], default=0))
        db_dict = {row[0]: row for row in db_data}
        
        for t in range(max_time + 1):
            backlog = autoscaler_data.get(t, {}).get('Backlog', 0)
            workers = autoscaler_data.get(t, {}).get('Workers', 0)
            db_row = db_dict.get(t, (t, 0, 0, 0, 0))
            writer.writerow([t, backlog, workers, db_row[1], f"{db_row[2]:.2f}", f"{db_row[3]:.2f}", f"{db_row[4]:.2f}"])
    
    cursor.close()
    conn.close()
except Exception as e:
    pass
```

### E. Visualizacion Local
**Archivo:** `graficos_locales.py`
**Proposito:** Generacion de graficas en alta resolucion requeridas por la rubrica academica.

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('FINAL_DATA_SCENARIO.csv')
plt.style.use('bmh')

# GRAFICA 1
plt.figure(figsize=(10, 5))
plt.plot(df['Time_Seconds'], df['Backlog'], color='#d62728', linewidth=2.5)
plt.title('Evolucion del Queue Backlog')
plt.savefig('grafico_1_backlog.png', dpi=300)

# GRAFICA 2
fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(df['Time_Seconds'], df['Throughput_Req_Sec'], color='#1f77b4', linewidth=2)
ax2 = ax1.twinx()
ax2.plot(df['Time_Seconds'], df['Active_Workers'], color='#ff7f0e', linewidth=2.5, linestyle='--')
plt.title('Elasticidad: Throughput y Workers')
plt.savefig('grafico_2_elasticidad.png', dpi=300)

# GRAFICA 3
plt.figure(figsize=(10, 5))
plt.plot(df['Time_Seconds'], df['Latency_p50_ms'], label='p50')
plt.plot(df['Time_Seconds'], df['Latency_p95_ms'], label='p95')
plt.plot(df['Time_Seconds'], df['Latency_p99_ms'], label='p99')
plt.title('Distribucion de Latencia')
plt.legend()
plt.savefig('grafico_3_latencia.png', dpi=300)
```

---

## 5. Pruebas y Experimentos (Experimental Setup)

Para cada uno de los tres escenarios exigidos, es obligatorio realizar un reseteo estricto del estado del sistema.

### Procedimiento de Prueba
1.  **Limpiar la infraestructura:**
    ```bash
    rm -f *.csv ; sudo docker exec -i postgres psql -U postgres -d postgres -c "UPDATE events SET available_tickets = 100000 WHERE event_id = 1; TRUNCATE TABLE processed_requests; TRUNCATE TABLE seats; INSERT INTO seats (event_id, seat_number, status) SELECT 1, generate_series(1, 100000), 'AVAILABLE';" ; sudo docker exec -i rabbitmq rabbitmqctl purge_queue ticket_orders
    ```
2.  **Iniciar Escalamiento:** `python3 aws_autoscaler.py`
3.  **Inyectar Carga:** `python3 producer.py` (Elegir Escenario 1, 2 o 3).
4.  **Generar CSV de Metricas:** `python3 master_csv.py`
5.  **Graficar Resultados Localmente:** `python graficos_locales.py`

## 6. Evaluacion de Fault Tolerance
El sistema garantiza las operaciones de compra procesando bajo semanticas transaccionales *At-least-once*:
* Las ordenes defectuosas o victimas de *Timeout* son reintroducidas a RabbitMQ (`basic_nack`).
* Los registros de ID previenen sobrecargas e inserciones duplicadas (Idempotencia transaccional).