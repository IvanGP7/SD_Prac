# Valor con la IP Pública actual de la instancia EC2 de AWS
AWS_EC2_IP = "13.216.244.177"

# Puertos estándar expuestos en los Security Groups
RABBITMQ_HOST = AWS_EC2_IP
RABBITMQ_PORT = 5672
QUEUE_NAME = "cola_insultos"

REDIS_HOST = AWS_EC2_IP
REDIS_PORT = 6379