from xmlrpc.server import SimpleXMLRPCServer
import random
import xmlrpc.client

insult_list = []
obs_urls = []

def registrar_observador(url):
    if url not in obs_urls:
        obs_urls.append(url)
        print(f"Nuevo observador registrado: {url}")
    return True

def add_insult(insult):
    nuevo = insult.lower()
    # Notificar a todos los archivos observadores externos
    for url in obs_urls:
        try:
            proxy = xmlrpc.client.ServerProxy(url)
            proxy.notificar(nuevo) # Llamamos a la función del observador
        except:
            print(f"Error notificando a {url}. ¿Está apagado?")

    if nuevo not in insult_list:
        insult_list.append(nuevo)
    return True

def get_insults():
    return insult_list

def insult_me():
    if not insult_list:
        return "Aún no hay insultos en la base de datos."
    return random.choice(insult_list)

# Crear el servidor XML-RPC
server = SimpleXMLRPCServer(("localhost", 8000))
print("Servidor escuchando en el puerto 8000...")
server = SimpleXMLRPCServer(("localhost", 8000), allow_none=True)
# Registrar las funciones que se pueden llamar desde el cliente
server.register_function(registrar_observador, "registrar_observador")
server.register_function(add_insult, "add_insult")
server.register_function(get_insults, "get_insults")
server.register_function(insult_me, "insult_me")

# Iniciar el servidor
server.serve_forever()