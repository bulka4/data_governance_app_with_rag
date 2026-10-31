// Redis client used to connect to Redis using redis_client.connect()

const redis = require('redis')

const redis_client = redis.createClient({
    url: process.env.REDIS_URL
})

redis_client.on('error', err => {
    console.error('Redis error:', err)
})

redis_client.on('ready', () => {
    console.log('Connection to Redis is ready');
});

module.exports = redis_client