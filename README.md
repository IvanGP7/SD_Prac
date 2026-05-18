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
