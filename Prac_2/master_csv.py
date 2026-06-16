import psycopg2
import csv
import glob
import os

DB_CONFIG = {"dbname": "postgres", "user": "postgres", "password": "admin", "host": "localhost", "port": "5432"}

try:
    # 1. Leer el CSV del autoescalador
    autoscaler_data = {}
    csv_files = glob.glob("scaling_metrics_*.csv")
    if csv_files:
        latest_csv = max(csv_files, key=os.path.getctime)
        with open(latest_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                autoscaler_data[int(row['Time_Seconds'])] = {
                    'Backlog': row['Backlog'],
                    'Workers': row['Active_Workers']
                }
    
    # 2. Conectar a BD y extraer latencias y throughput desde la fuente de verdad (Server-side)
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
        WHERE status = 'SUCCESS'
        GROUP BY time_sec
        ORDER BY time_sec;
    """)
    
    db_data = cursor.fetchall()
    
    # 3. Escribir el archivo CSV Unificado
    with open('FINAL_DATA_SCENARIO.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time_Seconds', 'Backlog', 'Active_Workers', 'Throughput_Req_Sec', 'Latency_p50_ms', 'Latency_p95_ms', 'Latency_p99_ms'])
        
        max_time = max(max(autoscaler_data.keys(), default=0), max([row[0] for row in db_data], default=0))
        db_dict = {row[0]: row for row in db_data}
        
        for t in range(max_time + 1):
            backlog = autoscaler_data.get(t, {}).get('Backlog', 0)
            workers = autoscaler_data.get(t, {}).get('Workers', 0)
            
            db_row = db_dict.get(t, (t, 0, 0, 0, 0))
            throughput = db_row[1]
            p50 = f"{db_row[2]:.2f}"
            p95 = f"{db_row[3]:.2f}"
            p99 = f"{db_row[4]:.2f}"
            
            writer.writerow([t, backlog, workers, throughput, p50, p95, p99])

    print("[+] Archivo 'FINAL_DATA_SCENARIO.csv' generado.")
    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error crítico: {e}")