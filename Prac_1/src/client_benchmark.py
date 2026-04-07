import Pyro4
import time
import sys

def run_benchmark(file_path):
    # Localizar el servidor mediante el Name Server
    try:
        server = Pyro4.Proxy("PYRONAME:concert.tickets")
    except Exception as e:
        print(f"Error conectando al servidor: {e}")
        return

    success_count = 0
    failure_count = 0
    
    print(f"Iniciando benchmark: {file_path}")
    start_time = time.time()

    with open(file_path, 'r') as f:
            for line in f:
                parts = line.split()
                if not parts: continue
                
                res = None  # Inicializamos res en cada vuelta

                # Formato Unnumbered: BUY <client_id> <request_id>
                if len(parts) == 3 and parts[0] == "BUY":
                    _, c_id, r_id = parts
                    res = server.buy_unnumbered(c_id, r_id)
                
                # Formato Numbered: BUY <client_id> <seat_id> <request_id>
                elif len(parts) == 4 and parts[0] == "BUY":
                    _, c_id, s_id, r_id = parts
                    res = server.buy_numbered(c_id, s_id, r_id)
                
                # Solo comprobamos res si se asignó algo (evita el UnboundLocalError)
                if res:
                    if res["status"] == "SUCCESS":
                        success_count += 1
                    else:
                        failure_count += 1

    end_time = time.time()
    total_time = end_time - start_time
    
    # Reporte de métricas (Requerimiento 8 de la práctica)
    print("\n--- RESULTADOS DEL BENCHMARK ---")
    print(f"Archivo: {file_path}")
    print(f"Tiempo total: {total_time:.2f} segundos")
    print(f"Throughput: {(success_count + failure_count) / total_time:.2f} ops/sec")
    print(f"Éxitos: {success_count} | Fallos: {failure_count}")
    print("--------------------------------\n")
    server.reset()  # Reiniciamos el sistema para la próxima ejecución

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python client_benchmark.py <ruta_del_archivo.txt>")
    else:
        run_benchmark(sys.argv[1])