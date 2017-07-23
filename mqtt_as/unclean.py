# clean.py Test of asynchronous mqtt client with clean session False.
# (C) Copyright Peter Hinch 2017.
# Released under the MIT licence.

# Public brokers https://github.com/mqtt/mqtt.github.io/wiki/public_brokers

# The use of clean_session = False means that during a connection failure
# the broker will queue publications with qos == 1 to the device. When
# connectivity is restored these will be transmitted. If this behaviour is not
# required, use a clean session (clean.py). (MQTT spec section 3.1.2.4).

# red LED: ON == WiFi fail
# blue LED heartbeat: demonstrates scheduler is running.
# Publishes connection statistics.

from mqtt_as import MQTTClient
import uasyncio as asyncio
import ubinascii
from machine import Pin, unique_id

SERVER = '192.168.0.9'  # Change to suit e.g. 'iot.eclipse.org'

CLIENT_ID = ubinascii.hexlify(unique_id())

wifi_led = Pin(0, Pin.OUT, value = 0)  # Red LED for WiFi fail/not ready yet
blue_led = Pin(2, Pin.OUT, value = 1)  # Message received

loop = asyncio.get_event_loop()

outages = 0

# Demonstrate scheduler is operational.
async def heartbeat():
    while True:
        await asyncio.sleep_ms(500)
        blue_led(not blue_led())

def sub_cb(topic, msg):
    print((topic, msg))

async def wifi_han(state):
    global outages
    wifi_led(state)  # Off == WiFi down (LED is active low)
    if state:
        print('WiFi is up.')
    else:
        outages += 1
        print('WiFi is down.')
    await asyncio.sleep(1)

async def conn_han(client):
    await client.subscribe('foo_topic', 1)

async def main(client):
    await client.connect()
    n = 0
    while True:
        await asyncio.sleep(5)
        print('publish', n)
        # If WiFi is down the following will pause for the duration.
        await client.publish('result', '{} repubs: {} outages: {}'.format(n, client.REPUB_COUNT, outages), qos = 1)
        n += 1

# Define configuration
mqtt_config = {'subs_cb':sub_cb,
    'wifi_coro': wifi_han,
    'will': ('result', 'Goodbye cruel world!', False, 0),
    'connect_coro': conn_han,
    'clean': False
    }

loop.create_task(heartbeat())
# Set up client
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(mqtt_config, CLIENT_ID, SERVER, keepalive = 120)

try:
    loop.run_until_complete(main(client))
finally:  # Prevent LmacRxBlk:1 errors.
    client.close()
