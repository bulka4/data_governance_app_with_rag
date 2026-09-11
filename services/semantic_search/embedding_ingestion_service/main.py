'''
The main() function runs an infinite loop that waits for Kafka messages and runs an embedding ingestion pipeline when a new message
appears indicating that a table description has been updated.

This pipeline ingests into a vector store embeddings for all documents from a document source database (full truncate and load).
This could be changed to updating embeddings only for a documentation for a specific table given by the 'table_id' field from the Kafka's 
message.

Kafka messages should have fields:
   - event_type - what event has happened. event_type = "table_description_created" means that a new table description was created
   - table_id - For event_type = "table_description_created", table_id indicates for which table a description was created
'''

import os

from KafkaMessageConsumer import KafkaMessageConsumer
from IngestionPipeline import IngestionPipeline


def main():
    # Kafka host to connect to
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    # kafka_group_id identifies the consumer group. All replicas of this service should use the same group ID
    kafka_group_id = 'embedding-ingestion-service'
    # Kafka topic to subscribe to (consumer will read messages from this topic)
    kafka_topic = os.getenv("KAFKA_TOPIC")

    mongo_host = os.getenv("MONGO_HOST")
    mongo_db = os.getenv("MONGO_DB")
    mongo_collection = os.getenv("MONGO_COLLECTION")

    download_model = os.getenv("DOWNLOAD_MODEL") == "True"
    model_name = os.getenv("MODEL_NAME")
    model_path = os.getenv("MODEL_PATH")

    milvus_host = os.getenv("MILVUS_HOST")
    milvus_collection = os.getenv("MILVUS_COLLECTION_NAME")
    milvus_embedding_field_name = os.getenv("EMBEDDING_FIELD_NAME")
    milvus_text_field_name = os.getenv("TEXT_FIELD_NAME")
    milvus_metadata_field_name = os.getenv("METADATA_FIELD_NAME")
    milvus_id_field_name = os.getenv("ID_FIELD_NAME")

    consumer = KafkaMessageConsumer(
        bootstrap_servers=bootstrap_servers,
        group_id=kafka_group_id,
        topic=kafka_topic,
    )

    ingestion_service = IngestionPipeline(
        mongo_host=mongo_host,
        mongo_db=mongo_db,
        mongo_collection=mongo_collection,
        download_model=download_model,
        model_name=model_name,
        model_path=model_path,
        milvus_host=milvus_host,
        milvus_collection=milvus_collection,
        milvus_embedding_field_name=milvus_embedding_field_name,
        milvus_text_field_name=milvus_text_field_name,
        milvus_metadata_field_name=milvus_metadata_field_name,
        milvus_id_field_name=milvus_id_field_name,
    )

    # Start receiving messages from a specific topic (given by the consumer.topic = kafka_topic)
    consumer.subscribe()

    print('Started listening to messages from Kafka')

    # consumer.consume() runs an infinite loop that waits for Kafka messages and yields them in a JSON format one at a time.
    # Those messages should have fields:
    #   - event_type - what event has happened. event_type = "table_description_created" means that a new table description was created
    #   - table_id - For event_type = "table_description_created", table_id indicates for which table a description was created
    for message in consumer.consume():
        print(f"Received a Kafka message: {message}")

        try:
            event_type = message["event_type"]
            table_id = message["table_id"]

            if event_type == "table_description_created":
                # Ingest embeddings for all the documents from the source document database. We could change it to update only the
                # document for the table given by the 'table_id' field from the Kafka's message.
                ingestion_service.ingest()

                # Commit the offset - i.e. save information that this was the last processed message, so when the service crashes, 
                # we know which messages were already processed.
                consumer.commit()

                print(f"Successfully ingested table descriptions after updating the table with ID: {table_id}")
        except Exception as e:
            print(f"Failed to process message: {e}")

            # Don't commit (i.e. don't mark this message as processed). Kafka will deliver the message again and we will 
            # try to process it again.


if __name__ == "__main__":
    main()