import Pyro4
import time
import sys

def run_balanced_benchmark(file_path, ip_servidor):
    # 1. Localizar el Name Server
    try:
        ns = Pyro4.locateNS(host=ip_servidor)
        # Buscamos todos los objetos registrados que empiecen por "concert.tickets"
        all_objects = ns.list(prefix="concert.tickets.")
        
        if not all_objects:
            print("Error: No se encontraron nodos (concert.tickets.nodo1, etc.) registrados.")
            return

        # Creamos una lista de proxies (conexiones) a cada nodo encontrado
        proxies = []
        for name in all_objects.keys():
            proxies.append(Pyro4.Proxy(f"PYRONAME:{name}"))
            #print(f"Conectado al nodo: {name}")

    except Exception as e:
        print(f"Error inicializando proxies: {e}")
        return

    num_nodes = len(proxies)
    current_node_index = 0
    success_count = 0
    failure_count = 0
    
    #print(f"Iniciando benchmark BALANCEADO ({num_nodes} nodos): {file_path}")
    start_time = time.time()

    with open(file_path, 'r') as f:
        for line in f:
            parts = line.split()
            if not parts or parts[0] != "BUY": continue
            
            # --- Lógica de Round-Robin ---
            # Seleccionamos el nodo actual y saltamos al siguiente para la próxima línea
            server = proxies[current_node_index]
            current_node_index = (current_node_index + 1) % num_nodes
            
            res = None
            # Formato Unnumbered: BUY <client_id> <request_id>
            if len(parts) == 3:
                _, c_id, r_id = parts
                res = server.buy_unnumbered(c_id, r_id)
            
            # Formato Numbered: BUY <client_id> <seat_id> <request_id>
            elif len(parts) == 4:
                _, c_id, s_id, r_id = parts
                res = server.buy_numbered(c_id, s_id, r_id)
            
            if res:
                if res["status"] == "SUCCESS":
                    success_count += 1
                else:
                    failure_count += 1

    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n--- RESULTADOS BENCHMARK DIRECTO BALANCEADO ---")
    print(f"Nodos utilizados: {num_nodes}")
    print(f"Archivo: {file_path}")
    print(f"Tiempo total: {total_time:.2f} segundos")
    print(f"Throughput: {(success_count + failure_count) / total_time:.2f} ops/sec")
    print(f"Éxitos: {success_count} | Fallos: {failure_count}")
    print("----------------------------------------------\n")
    server.reset()  # Reiniciamos el sistema para la próxima ejecución

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python client_benchmark_balanced.py <ruta_del_archivo.txt> <ip_del_servidor>")
    else:
        run_balanced_benchmark(sys.argv[1], sys.argv[2])