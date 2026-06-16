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

### B. Autoescalador Dinamico
**Archivo:** `aws_autoscaler.py`
**Proposito:** Monitorizar RabbitMQ y escalar AWS Lambda concurrentemente basandose en la ecuacion de rendimiento.

### C. Simulador de Carga Z(t)
**Archivo:** `producer.py`
**Proposito:** Inyectar perfiles de carga (Uniform y Hotspot) y simular fases de elasticidad.

### D. Extractor Server-Side Metrics
**Archivo:** `master_csv.py`
**Proposito:** Combinar datos de autoescalado con latencia real end-to-end extraida nativamente desde PostgreSQL.

### E. Visualizacion Local
**Archivo:** `graficos_locales.py`
**Proposito:** Generacion de graficas en alta resolucion requeridas por la rubrica academica.

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