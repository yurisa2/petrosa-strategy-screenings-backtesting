from kafka import KafkaConsumer
consumer = KafkaConsumer('binance_socket_prices',
                         bootstrap_servers='localhost:9093')
for msg in consumer:
    print(msg)
