'''
HomeStation MicroPython Code
Written by Liam Howell
Project Write-up: https://core-electronics.com.au/projects/homestation/
Full Repo: https://github.com/LiamHowell/HomeStation

Should host a web-page with Sensor readouts, and a colour picker for the RGB Module

Adapted from the adaptation:
https://core-electronics.com.au/projects/wifi-garage-door-controller-with-raspberry-pi-pico-w-smart-home-project/
    Adapted from examples in: https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf
'''

import network
import uasyncio as asyncio
from machine import Pin


from homestation import *

from PiicoDev_Unified import sleep_ms

from PiicoDev_SSD1306 import * 
from PiicoDev_BME280 import PiicoDev_BME280
from PiicoDev_VEML6030 import PiicoDev_VEML6030
from PiicoDev_RGB import PiicoDev_RGB, wheel

# Create PiicoDev sensor objects
atmo = PiicoDev_BME280()
lght = PiicoDev_VEML6030()
leds = PiicoDev_RGB()

try:
    display = create_PiicoDev_SSD1306()
except:
    print('OLED not plugged in')





def showIP(ipStr):
    try:
        display.text(ipStr, 0,0, 1)
        display.show()
    except:
        print('OLED not plugged in')


# Configure your WiFi SSID and password
ssid = 'projectRouter'
password = 'password1'

check_interval_sec = 0.25

wlan = network.WLAN(network.STA_IF) ## Pass in wlan?

wlan_param = [wlan,ssid,password]

def lstStrSensors(atmo,lght):
    tempC, preshPa, humRH, lux = getSensors(atmo,lght)
    return ["Temp: {:.1f} &#8451;".format(tempC),"Press: {:.0f}hPa".format(preshPa),"RH: {:.1f}%".format(humRH),"Lux: {:.1f}".format(lux)]

# Get converted Atmo Data
def getAtmo(atmo):
    tempC, presPa, humRH = atmo.values()
    return tempC, presPa/100, humRH #[degC,hPa,RH]

# Get Lux data
def getLight(lght):
    return lght.read() # Lux

def atmoSplit():
    tempC, presPa, humRH = atmo.values()
    return tempC, presPa/100, humRH #[degC,hPa,RH]


# sensorData = {
#     ".Atmo": atmoSplit,
#     "Temperature :": ['Atmo',0],
#     "Pressure": ['Atmo',1],
#     "Humidity": ['Atmo',2],
#     "Light": lght.read,
# }


#Push the RBG Value to the RGB module and show it
def pushLight(leds,colLst):
    leds.setPixel(0, colLst[0])
    leds.setPixel(1, colLst[1])
    leds.setPixel(2, colLst[2])
    leds.show()

def strToLight(a):
    hex_pref = '0x'
    return [int(hex_pref+a[0:2]),int(hex_pref+a[2:4]),int(hex_pref+a[4:6])]

def getSensors(atmo,lght): # CHANGE THIS TO A DICT, key is the text and value is the reading
    tempC, preshPa, humRH = getAtmo(atmo)
    return [tempC, preshPa, humRH, getLight(lght)]

sensorData = 'Update plox'

async def main():
    print('Connecting to WiFi...')
    asyncio.create_task(connect_to_wifi(wlan_param))

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(lambda r,w: serve_client(r,w,sensors=sensorData), "0.0.0.0", 80))

    while True:
        await asyncio.sleep(check_interval_sec)


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()

