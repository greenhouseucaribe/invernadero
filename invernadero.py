import pika

MAX_ITERACIONES = 3
iteraciones = 0

class Chile:
    def __init__(self):
        self.temperatura = 0
        self.humedad = 0
        self.vida = 30

    def establecer_valores(self, temperatura, humedad):
        self.temperatura = temperatura
        self.humedad = humedad

    def disminuir_vida(self):
        self.vida -= 5

    def __str__(self):
        return f"Temperatura: {self.temperatura}, Humedad: {self.humedad}, Vida: {self.vida}"

def verificar_germinacion(chiles):
    for i in range(3):
        for j in range(3):
            if chiles[i][j].vida > 10:
                print(f"El chile en la casilla ({i}, {j}) germinó.")
            else:
                print(f"El chile en la casilla ({i}, {j}) no germinó.")

def process_data(ch, method, properties, body):
    data = eval(body.decode())
    print(f"\nInvernadero recibiendo datos {data}")

    for i in range(3):
        for j in range(3):
            chiles[i][j].establecer_valores(data['temperatura'][3*i + j], data['humedad'][3*i + j])
            print(f"Chile en casilla ({i}, {j}): {chiles[i][j]}")

    # Enviar datos a actuadores
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='172.20.10.4', port=5672))
    channel = connection.channel()
    channel.queue_declare(queue='actuadores')
    channel.basic_publish(exchange='', routing_key='actuadores', body=str(data))
    connection.close()

# Matriz de chiles
chiles = [[Chile() for _ in range(3)] for _ in range(3)]

connection = pika.BlockingConnection(pika.ConnectionParameters(host='172.20.10.4', port=5672))
channel = connection.channel()

# Escuchar datos de la API
channel.queue_declare(queue='invernadero')
channel.basic_consume(queue='invernadero', on_message_callback=process_data, auto_ack=True)

# Escuchar datos de actuadores (resultados)
def process_actuator_data(ch, method, properties, body):
    global iteraciones
    data = eval(body.decode())
    print("\nDatos actualizados por actuadores:")
    for i in range(3):
        for j in range(3):
            chiles[i][j].establecer_valores(data['temperatura'][3*i + j], data['humedad'][3*i + j])
            
            if not(25 <= chiles[i][j].temperatura <= 30) or not(50 <= chiles[i][j].humedad <= 70):
                chiles[i][j].disminuir_vida()

            print(f"Chile en casilla ({i}, {j}): {chiles[i][j]}")

    iteraciones += 1
    if iteraciones >= MAX_ITERACIONES:
        verificar_germinacion(chiles)
        ch.stop_consuming()

channel.queue_declare(queue='invernadero_results')
channel.basic_consume(queue='invernadero_results', on_message_callback=process_actuator_data, auto_ack=True)

print('Invernadero esperando datos...')
channel.start_consuming()