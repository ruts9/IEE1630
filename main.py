import pycom
from network import WLAN
import machine
from machine import UART
import time
from mqtt import MQTTClient

# ENTER WIFI NAME AND PASSWORD and Ubidots token HERE!!!
WIFI_Name = "Kodu"
WIFI_Password = "P6ldma235"
Ubidots_token = "BBFF-Ew0cOcWxY3scPeKuxYY9Yvb8DPmD9s"
# ENTER WIFI NAME AND PASSWORD and Ubidots token HERE!!!

# INIT UART
pycom.heartbeat(False)
# Set the baudrate to 9600, and TX to pin 22 and RX to 21
uart = UART(1, baudrate=9600, pins=('P22', 'P21'))
print("UART INIT DONE")

def configSensor():
    #This sets the range of the measured CO2 ppm from 0 - 10 000 .
    uart.write(b'\xff\x01\x99\x00\x00\x00\x27\x10\x2F')

# Configure the sensor
configSensor()
print("Sensor configured")

def measureCO2():
    # This hex value asks the CO2 reading from sensor.
    uart.write(b'\xff\x01\x86\x00\x00\x00\x00\x00\x79')
    # Wait for sensor to awnser
    time.sleep(0.1)
    # Read the value
    rawValue = uart.read(9)
    return rawValue
    
#Convert raw data to correct data    
def rawdata2PPM(input):
    # CO2 concentration = HIGH Byte * 256 + LOW Byte
    ppm = input[2] * 256 + input[3]
    return ppm

#Connect to WIFI
wlan = WLAN(mode=WLAN.STA)
wlan.connect(WIFI_Name, auth=(WLAN.WPA2, WIFI_Password), timeout=5000)
print("Connected to WIFI")

#MQTT callback
def sub_cb(topic, msg):
   print(msg)

# if not connected to wifi, set machine as idle/inactive
while not wlan.isconnected():
    machine.idle()

# Connect to MQTT client in ubidots, unique token to send the data to.
client = MQTTClient("ubidotsclient", "things.ubidots.com",user= Ubidots_token, password="", port=1883)
print("Connected to Ubidots")
client.set_callback(sub_cb)
client.connect()

configSensor()
while True:
    # Get data from sensor
    ppm = rawdata2PPM(measureCO2())
    # Send data to Ubidots
    client.publish("/v1.6/devices/pycomCO2", '{"CO2": ' + str(ppm) +'}')
    # Just to not overflow the data, as Ubidots allows 4000 data points per day for free accounts
    time.sleep(0.5)
    print(ppm)