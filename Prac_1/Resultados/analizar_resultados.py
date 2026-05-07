import matplotlib.pyplot as plt
import os
import re
import sys

def analizar():
    carpeta = os.path.join("Prac_1", "Resultados")
    if len(sys.argv) > 1:
        ruta_arg = sys.argv[1]
        carpeta = os.path.dirname(ruta_arg) if os.path.isfile(ruta_arg) else ruta_arg

    nodos_eje = []
    data_directo = {}
    data_indirecto = {}

    print(f"Procesando datos de: {os.path.abspath(carpeta)}")

    for archivo in os.listdir(carpeta):
        if not archivo.endswith(".txt"): continue
        
        # Extraer número de nodos del nombre del archivo
        n_match = re.search(r"(\d+)", archivo)
        if not n_match: continue
        n = int(n_match.group(1))
        if n not in nodos_eje: nodos_eje.append(n)

        ruta = os.path.join(carpeta, archivo)
        with open(ruta, 'r', encoding='utf-16') as f:
            es_indirecto = False
            es_20k = False
            
            for linea in f:
                l_up = linea.upper()
                
                # 1. Identificar Arquitectura
                if "DIRECTO" in l_up: es_indirecto = False
                if "INDIRECTO" in l_up or "RABBITMQ" in l_up: es_indirecto = True
                
                # 2. Identificar si es el test de 20k (Unnumbered)
                if "20000" in linea: es_20k = False
                if "60000" in linea: es_20k = True # Resetear si entramos en el de 60k
                
                # 3. Capturar el Throughput solo si estamos en el bloque de 20k
                if "THROUGHPUT" in l_up and es_20k:
                    val_match = re.search(r"([\d.]+)", linea)
                    if val_match:
                        valor = float(val_match.group(1))
                        if es_indirecto:
                            data_indirecto[n] = valor
                        else:
                            data_directo[n] = valor

    nodos_eje.sort()
    
    # --- GENERAR GRÁFICO ---
    plt.figure(figsize=(10, 6))
    
    # Línea Directo (Pyro4)
    vals_dir = [data_directo.get(n, 0) for n in nodos_eje]
    plt.plot(nodos_eje, vals_dir, 'o-', label='Directo (Pyro4)', color='#3498db', linewidth=2, markersize=8)
    
    # Línea Indirecto (RabbitMQ)
    vals_ind = [data_indirecto.get(n, 0) for n in nodos_eje]
    plt.plot(nodos_eje, vals_ind, 's-', label='Indirecto (RabbitMQ)', color='#e67e22', linewidth=2, markersize=8)

    # Añadir etiquetas de texto
    for n in nodos_eje:
        if n in data_directo:
            plt.annotate(f'{data_directo[n]}', (n, data_directo[n]), textcoords="offset points", xytext=(0,10), ha='center', color='#2980b9', fontsize=9)
        if n in data_indirecto:
            plt.annotate(f'{data_indirecto[n]}', (n, data_indirecto[n]), textcoords="offset points", xytext=(0,10), ha='center', color='#d35400', fontsize=9)

    plt.title('Escalabilidad del Sistema: Throughput vs Nodos (60k Numbered)', fontsize=14, fontweight='bold')
    plt.xlabel('Número de Nodos / Workers', fontsize=12)
    plt.ylabel('Peticiones por segundo (ops/sec)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='upper left')
    plt.xticks(nodos_eje)
    
    plt.tight_layout()
    plt.savefig('grafico_escalabilidad_final.png')
    print(f"[+] Gráfico guardado como 'grafico_escalabilidad_final.png'")
    plt.show()

if __name__ == "__main__":
    analizar()