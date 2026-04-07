import xmlrpc.client

# Conexion con el servidor
s = xmlrpc.client.ServerProxy('http://localhost:8000', allow_none=True)

# Llamar a funciones de test
for i in range (1,10):
    s.add_insult(f"insult_{i}")

insult = s.insult_me()

insult_list = s.get_insults()

print(f"Insulto recibido por el servidor: {insult}\n")
print(f"Lista de insultos del servidor: {insult_list}\n")