'''
A class for the Kafka message consumer - a process that waits for messages from Kafka and reads their data when they arrive.
'''

from confluent_kafka import Consumer
import json


class KafkaMessageConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topic: str
    ):
        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            # Don't consider a message processed before the embedding ingestion succeeds.
            "enable.auto.commit": False,
            # For debugging only
            # "debug": "broker,protocol,cgrp",
            # "error_cb": self.error_callback,
        })

        self.topic = topic

    def error_callback(self, error):
        # For debugging
        print(f"Kafka error callback: {error}", flush=True)

    def subscribe(self):
        print("Subscribing to a topic", flush=True)
        # Start receiving messages from a specific topic
        self.consumer.subscribe([self.topic])
        print("Subscribed to a topic", flush=True)

    def consume(self):
        print("Starting poll loop", flush=True)

        # Infinite loop that waits for Kafka messages and yields them as a dictionary one at a time.
        while True:
            # print("Polling...", flush=True)
            # Check whether a message is available (wait 1 sec for a message to arrive)
            message = self.consumer.poll(1.0)

            # print(f"Poll returned: {message}", flush=True)

            if message is None:
                continue

            if message.error():
                print(f"Kafka error: {message.error()}")
                continue

            yield json.loads(message.value().decode("utf-8"))

    def commit(self):
        # Commit the offset - i.e. save information that this was the last processed message, so when the service crashes, 
        # we know which messages were already processed.
        self.consumer.commit()