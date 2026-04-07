# 
# Panel de Control para Venta de Entradas - Worker:
#   - Implementa la lógica de compra de entradas (No Numeradas y Numeradas).
#   - Utiliza Redis para manejar el estado de las ventas y asegurar la consistencia.
#   - Se conectara con los middlewares sindo llamado por el servidor en el caso de la arquitectura Directa y por el cliente en la arquitectura Indirecta.
# Funciones:
#   - buy_unnumbered(client_id, request_id): Maneja la compra de entradas no numeradas.
#   - buy_numbered(client_id, seat_id, request_id): Maneja la compra de entradas numeradas.
#   - reset_system(): Limpia la base de datos para una nueva ejecución del benchmark.
#   - get_statistics(): Devuelve el estado actual para los reportes.

import redis

class TicketWorker:
    def __init__(self, host='localhost', port=6379):
        # Conexión a Redis. decode_responses=True para manejar strings directamente.
        self.r = redis.Redis(host=host, port=port, decode_responses=True)
        self.TOTAL_TICKETS = 20000
        self.COUNTER_KEY = "tickets:unnumbered:count"
        self.MAP_KEY = "tickets:numbered:map"

    def reset_system(self):
        self.r.delete(self.COUNTER_KEY, self.MAP_KEY)
        print("Sistema Reiniciado: Redis limpio.")

    # MODELO Directo: TICKETS NO NUMERADOS
    def buy_unnumbered(self, client_id, request_id):
        # Incrementamos el contador
        current_count = self.r.incr(self.COUNTER_KEY)

        if current_count <= self.TOTAL_TICKETS:
            # Éxito: Guardamos registro opcionalmente para auditoría
            return {"status": "SUCCESS", "client": client_id, "req_id": request_id, "ticket": current_count}
        else:
            # Fallo: Superado el límite
            return {"status": "SOLD_OUT", "client": client_id, "req_id": request_id}

    # MODELO Indirecto: TICKETS NUMERADOS
    def buy_numbered(self, client_id, seat_id, request_id):

        if int(seat_id) < 1 or int(seat_id) > self.TOTAL_TICKETS:
            return {"status": "INVALID_SEAT", "client": client_id, "seat": seat_id, "req_id": request_id}
        
        # Intentamos asignar el client_id al seat_id solo si está vacío
        was_set = self.r.hsetnx(self.MAP_KEY, seat_id, client_id)

        if was_set:
            return {"status": "SUCCESS", "client": client_id, "seat": seat_id, "req_id": request_id}
        else:
            # El asiento ya estaba ocupado
            return {"status": "SEAT_TAKEN", "client": client_id, "seat": seat_id, "req_id": request_id}

    def get_statistics(self):
        # Devuelve el estado actual para los reportes.
        unnumbered = int(self.r.get(self.COUNTER_KEY) or 0)
        numbered = self.r.hlen(self.MAP_KEY)
        return {
            "unnumbered_sold": min(unnumbered, self.TOTAL_TICKETS),
            "numbered_sold": numbered
        }