# SD_Prac
## Guía de Ejecución Distribuida (Dos Máquinas)

Esta sección describe cómo ejecutar los benchmarks utilizando dos máquinas físicas (p. ej., Torre como Servidor y Portátil como Cliente) para validar la escalabilidad y el comportamiento del sistema en red.

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

Bash
python server_direct.py [IP_SERVIDOR] concert.tickets.nodo1
python server_direct.py [IP_SERVIDOR] concert.tickets.nodo2
3. Lanzar Workers de Arquitectura Indirecta (RabbitMQ)
Bash
python server_indirect.py
### Fase 2: Ejecución del Benchmark (Máquina B - Portátil)
Desde la máquina cliente, lanza las pruebas apuntando a la IP de la torre:

1. Limpiar Sistema (Opcional)
```Bash
python limpiar.py [IP_SERVIDOR]
```
2. Benchmark Arquitectura Directa (Balanceado)
```Bash
python client_benchmark_balanced.py benchmark_unnumbered.txt [IP_SERVIDOR]
```
3. Benchmark Arquitectura Indirecta (RabbitMQ)
```Bash
python client_benchmark_indirect.py benchmark_unnumbered.txt [IP_SERVIDOR]
```
Análisis de Resultados Esperados
Escalabilidad Pyro4: El throughput debería mejorar ligeramente al añadir nodos, pero se verá limitado por el coste de gestión de proxies en el cliente y la latencia de red.

Escalabilidad RabbitMQ: Al añadir más workers en la Máquina A, el tiempo total de procesamiento en el benchmark indirecto debería reducirse de forma casi lineal.

Consistencia: En ambos modelos, el reporte final debe indicar 0 errores de duplicidad de asientos gracias a la atomicidad de Redis.
