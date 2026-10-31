const { Kafka } = require("kafkajs");

const kafka = new Kafka({
    clientId: "table-api",
    brokers: ["kafka:9092"]
});

const producer = kafka.producer();

async function connect() {
    await producer.connect();
}

async function publishTableDescriptionCreated(tableId) {
    // Emit an event to Kafka that a table description has been changed
    await producer.send({
        topic: process.env.KAFKA_TOPIC,
        messages: [
            {
                key: tableId,
                value: JSON.stringify({
                    event_type: "table_description_created",
                    table_id: tableId
                })
            }
        ]
    });

    console.log('message sent')
}

module.exports = {
    connect,
    publishTableDescriptionCreated
};