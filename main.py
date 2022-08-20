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
import time

# import custWebpage # TODO

from PiicoDev_Unified import sleep_ms

from PiicoDev_BME280 import PiicoDev_BME280
from PiicoDev_VEML6030 import PiicoDev_VEML6030
from PiicoDev_RGB import PiicoDev_RGB, wheel

# Create PiicoDev sensor objects
atmo = PiicoDev_BME280()
lght = PiicoDev_VEML6030()
leds = PiicoDev_RGB()

led = Pin("LED", Pin.OUT, value=1)



# Configure your WiFi SSID and password
ssid = 'projectRouter'
password = 'password1'

check_interval_sec = 0.25

wlan = network.WLAN(network.STA_IF)

# html = """<!DOCTYPE html>
# <html>
# <head> <title>Pico W</title> </head>
# <body> <h1>Pico W</h1>
# <p>Hello World</p>
# </body>
# </html>
# """

html = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>PicoW | HomeStation</title></head>
<body> <h2>HomeStation</h2>
<p id="sensors">NA</p>
{script}
</body>
</html>
"""

script = '''<script>
    
setInterval(function() {
  getSensors(); <!-- call a function with set ms updates -->
}, 2000);

function getSensors() {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      document.getElementById("sensors").innerHTML = this.responseText;
    }
  };
  xhttp.open("GET", "sensors", true);
  xhttp.send();
}
</script>
'''

def requestBreakdown(request):
    return request.split()


def blink_led(frequency = 0.5, num_blinks = 3):
    for _ in range(num_blinks):
        led.on()
        time.sleep(frequency)
        led.off()
        time.sleep(frequency)


async def connect_to_wifi():
    wlan.active(True)
    wlan.config(pm = 0xa11140)  # Diable powersave mode
    wlan.connect(ssid, password)
    
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    # Handle connection error
    if wlan.status() != 3:
        blink_led(0.1, 10)
        raise RuntimeError('WiFi connection failed')
    else:
        blink_led(0.5, 2)
        print('connected')
        status = wlan.ifconfig()
        print('ip = ' + status[0])


async def serve_client(reader, writer):
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass
    request = str(request_line)
    
    
    cmd_rq = requestBreakdown(request)
    
    print(cmd_rq[1])
    stateis = htmlifyLstStr(lstStrSensors(atmo,lght))
    
    
    
    
    if cmd_rq[1] == '/':
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        response = html.format(script=script)
        writer.write(response)
        
    elif cmd_rq[1] == '/sensors':
        sensorUpdateStr = htmlifyLstStr(lstStrSensors(atmo,lght))
        writer.write(sensorUpdateStr)
    
    
    
    
#     stateis = htmlifyLstStr(lstStrSensors(atmo,lght))
#     response = html.format(script=script)
#     
#     #print(response)
#     cmd_sensorUpdate = request.find('/sensor')
#     
#     if cmd_sensorUpdate ==8:
#         print('rquest up')
#         writer.write(response)
#     
#     #sensorUpdateStr = htmlifyLstStr(lstStrSensors(atmo,lght))
#     
#     
#     writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
#     writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")



# TODO Wrap into custom function

# Get converted Atmo Data
def getAtmo(atmo):
    tempC, presPa, humRH = atmo.values()
    return tempC, presPa/100, humRH #[degC,hPa,RH]

# Get Lux data
def getLight(lght):
    return lght.read() # Lux

#Push the RBG Value to the RGB module and show it
def pushLight(leds,colLst):
    leds.setPixel(0, colLst[0])
    leds.setPixel(1, colLst[1])
    leds.setPixel(2, colLst[2])
    leds.show()

def getSensors(atmo,lght):
    tempC, preshPa, humRH = getAtmo(atmo)
    return [tempC, preshPa, humRH, getLight(lght)]

def lstStrSensors(atmo,lght):
    tempC, preshPa, humRH, lux = getSensors(atmo,lght)
    return ["Temp: {:.1f} &#8451;".format(tempC),"Press: {:.0f}hPa".format(preshPa),"RH: {:.1f}%".format(humRH),"Lux: {:.1f}".format(lux)]

def htmlifyLstStr(lst):
    sensStr = ''
    for x in lst:
        sensStr += '<p>'
        sensStr += x
        sensStr += '</p>'
    return sensStr

# aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaah

async def main():
    print('Connecting to WiFi...')
    asyncio.create_task(connect_to_wifi())

    print('Setting up webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))

    while True:
        await asyncio.sleep(check_interval_sec)


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()

