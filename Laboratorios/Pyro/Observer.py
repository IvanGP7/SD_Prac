import Pyro4
import uuid

@Pyro4.expose
class MiObserver(object):
    def notificar(self, insulto):
        print(f"¡AVISO! El servidor recibió: {insulto}")

# Cada observador necesita su propio Daemon para que el central lo llame
daemon = Pyro4.Daemon()
mi_uri = daemon.register(MiObserver)

# Nos conectamos al central para decirle "aquí estoy, llámame a esta URI"
central = Pyro4.Proxy("PYRONAME:server.central")
central.registrar_observador(mi_uri)

print("Observador esperando notificaciones...")
daemon.requestLoop()