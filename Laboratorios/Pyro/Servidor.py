import Pyro4

@Pyro4.expose
class ServidorCentral(object):
    def __init__(self):
        self.insultos = []
        self.observadores = [] # Aquí guardaremos los proxies de los observers

    def registrar_observador(self, uri_observador):
        # Convertimos la URI en un objeto real que podemos usar
        nuevo_obs = Pyro4.Proxy(uri_observador)
        self.observadores.append(nuevo_obs)
        print(f"Nuevo observador conectado: {uri_observador}")
        return "Registrado con éxito"

    def add_insult(self, insulto):
        self.insultos.append(insulto)
        # Notificar a todos los objetos remotos
        for obs in self.observadores:
            try:
                obs.notificar(insulto)
            except:
                print("Un observador se desconectó.")
        return "Insulto procesado"

# Registro en el Name Server
daemon = Pyro4.Daemon()
ns = Pyro4.locateNS()
uri = daemon.register(ServidorCentral())
ns.register("server.central", uri)

print("Servidor Central Pyro4 esperando...")
daemon.requestLoop()