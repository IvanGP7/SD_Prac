from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import sys

# Pedimos el puerto por consola para poder abrir varios
if len(sys.argv) < 2:
    print("Uso: python observador.py [puerto]")
    sys.exit()

PUERTO = int(sys.argv[1])
MI_URL = f"http://localhost:{PUERTO}"

# 1. Definimos qué hacer cuando el servidor nos avise
def notificar(insulto):
    print(f"¡AVISO RECIBIDO! Alguien envió: {insulto}")
    return True

# 2. Creamos un servidor interno para "escuchar" al servidor central
obs_server = SimpleXMLRPCServer(("localhost", PUERTO), allow_none=True, logRequests=False)
obs_server.register_function(notificar, "notificar")

# 3. Nos registramos en el servidor central
try:
    cliente_al_central = xmlrpc.client.ServerProxy('http://localhost:8000')
    cliente_al_central.registrar_observador(MI_URL)
    print(f"Observador listo en {MI_URL}. Esperando insultos...")
    obs_server.serve_forever()
except Exception as e:
    print(f"Error: Asegúrate de que el servidor central esté corriendo. {e}")