import Pyro4
from Worker import TicketWorker

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")  # Instancia única para mantener la conexión a Redis
class TicketServer(object):
    def __init__(self):
        self.worker = TicketWorker(host='localhost') # Cambia 'localhost' por la IP de la VM de Redis

    def buy_unnumbered(self, client_id, request_id):
        print(f"Recibida solicitud BUY UNNUMBERED: client_id={client_id}, request_id={request_id}")
        return self.worker.buy_unnumbered(client_id, request_id)

    def buy_numbered(self, client_id, seat_id, request_id):
        print(f"Recibida solicitud BUY NUMBERED: client_id={client_id}, seat_id={seat_id}, request_id={request_id}")
        return self.worker.buy_numbered(client_id, seat_id, request_id)

    def reset(self):
        self.worker.reset_system()
        return "OK"

def main():
    # Configuración del Daemon para aceptar conexiones externas (importante para AWS)
    # Reemplaza '0.0.0.0' por la IP privada de la VM si es necesario
    daemon = Pyro4.Daemon(host="127.0.0.1")
    ns = Pyro4.locateNS()
    
    uri = daemon.register(TicketServer)
    ns.register("concert.tickets", uri)

    print(f"Servidor Directo (Pyro4) listo.\nURI: {uri}")
    daemon.requestLoop()

if __name__ == "__main__":
    main()