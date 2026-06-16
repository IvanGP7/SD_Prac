import pandas as pd
import matplotlib.pyplot as plt
import os

archivo_csv = 'FINAL_DATA_SCENARIO.csv'

if not os.path.exists(archivo_csv):
    print(f"[X] Error: No se encuentra el archivo '{archivo_csv}'.")
    exit()

df = pd.read_csv(archivo_csv)
plt.style.use('bmh')

# GRÁFICA 1: Queue Backlog vs Time
plt.figure(figsize=(10, 5))
plt.plot(df['Time_Seconds'], df['Backlog'], color='#d62728', linewidth=2.5)
plt.title('Evolución del Queue Backlog', fontsize=14, fontweight='bold')
plt.xlabel('Tiempo (Segundos)', fontsize=12)
plt.ylabel('Mensajes en Cola (Backlog)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('grafico_1_backlog.png', dpi=300)

# GRÁFICA 2: Throughput y Workers vs Tiempo (Eje Doble para Elasticidad)
fig, ax1 = plt.subplots(figsize=(10, 5))
color_throughput = '#1f77b4'
ax1.set_xlabel('Tiempo (Segundos)', fontsize=12)
ax1.set_ylabel('Throughput (Peticiones / Segundo)', color=color_throughput, fontsize=12, fontweight='bold')
ax1.plot(df['Time_Seconds'], df['Throughput_Req_Sec'], color=color_throughput, linewidth=2, label='Throughput')
ax1.tick_params(axis='y', labelcolor=color_throughput)
ax1.grid(True, linestyle='--', alpha=0.7)

ax2 = ax1.twinx()
color_workers = '#ff7f0e'
ax2.set_ylabel('Active Workers (Lambdas)', color=color_workers, fontsize=12, fontweight='bold')
ax2.plot(df['Time_Seconds'], df['Active_Workers'], color=color_workers, linewidth=2.5, linestyle='--', label='Workers')
ax2.tick_params(axis='y', labelcolor=color_workers)
ax2.set_ylim(bottom=0)

plt.title('Elasticidad: Throughput y Workers a lo largo del tiempo', fontsize=14, fontweight='bold')
fig.tight_layout()
plt.savefig('grafico_2_elasticidad.png', dpi=300)

# GRÁFICA 3: Latency Percentiles (p50, p95, p99)
plt.figure(figsize=(10, 5))
plt.plot(df['Time_Seconds'], df['Latency_p50_ms'], label='p50 (Mediana)', color='#2ca02c', linewidth=2)
plt.plot(df['Time_Seconds'], df['Latency_p95_ms'], label='p95', color='#ff7f0e', linewidth=2)
plt.plot(df['Time_Seconds'], df['Latency_p99_ms'], label='p99', color='#9467bd', linewidth=2)
plt.title('Distribución de Latencia (Tiempo End-to-End)', fontsize=14, fontweight='bold')
plt.xlabel('Tiempo (Segundos)', fontsize=12)
plt.ylabel('Latencia (Milisegundos)', fontsize=12)
plt.legend(loc='upper right', fontsize=10)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('grafico_3_latencia.png', dpi=300)

plt.show()