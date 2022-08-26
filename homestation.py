'''
HomeStation MicroPython Library
Written by Liam Howell
Project Write-up: https://core-electronics.com.au/projects/homestation/
Full Repo: https://github.com/LiamHowell/HomeStation

Should host a web-page with Sensor readouts, and a colour picker for the RGB Module

Adapted from the adaptation:
https://core-electronics.com.au/projects/wifi-garage-door-controller-with-raspberry-pi-pico-w-smart-home-project/
Adapted from examples in: https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf
'''




'''
TODO
# Break code into classes - seperate ones for async tasks, loading the webserver, and generating the content
# Finish standardisation of the input functions (raw string/dict/ named tuple?/both?)
# Add some easy input options - button, RGB, text input
# Create a template sensor and input part of the webpage, java gets locked in regardless
# Make the page look cleaner
# Make the blink status indicate what is happening more clearly, document this
# Add 2 levels of optional debugging - print statements and optional OLED code for each, pass out with a getter function? ref PiicoDev

Functions
# General creation of webserver - input WLAN?
Sensor data - input dict
'''

from machine import Pin
import time

led = Pin("LED", Pin.OUT, value=1)

oled = False
try:
    from PiicoDev_SSD1306 import *
    oled = True
except:
    print('Could not init OLED')
    
if oled:
    display = create_PiicoDev_SSD1306()
    def showIP(ipStr):
        try:
            display.text(ipStr, 0,0, 1)
            display.show()
        except:
            print('OLED not plugged in')
        
def getSensors(sensorDict):
    sensorOut = {}
    for i,j in sensorDict.items():
        if callable(j):
            sensorOut[i]=j()
        elif type(j) == type([]):
            sensorOut[i] = sensorOut.get('.'+j[0])[j[1]]
    return sensorOut 



# def buildSensorHTML():
#     
    

def blink_led(frequency = 0.5, num_blinks = 3):
    for _ in range(num_blinks):
        led.on()
        time.sleep(frequency)
        led.off()
        time.sleep(frequency)
    
    
def requestBreakdown(request):
    return request.split()

def strToLight(a):
    hex_pref = '0x'
    return [int(hex_pref+a[0:2]),int(hex_pref+a[2:4]),int(hex_pref+a[4:6])]

async def connect_to_wifi(wlan_param):
    wlan, ssid, passw = wlan_param
    wlan.active(True)
    wlan.config(pm = 0xa11140)  # Diable powersave mode
    wlan.connect(ssid, passw)
    
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('Waiting for connection...')
        time.sleep(1)

    # Handle connection error
    if wlan.status() != 3:
        blink_led(0.1, 10)
        raise RuntimeError('WiFi connection failed')
    else:
        blink_led(0.5, 2)
        print('Connected')
        status = wlan.ifconfig()
        print('IP = ' + status[0])
        showIP(status[0])

async def serve_client(reader, writer, sensors=None):
    print(type(sensors))
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass
    request = str(request_line)
    cmd_rq = requestBreakdown(request)
    
    if cmd_rq[1] == '/': #Make 2 standard ones and the option to add more easily
        writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        response = html.format(sensors=sensors,script=script,colour=colour)
        #pushLight(leds,[[0,0,0]]*3)
        writer.write(response)
        
    elif cmd_rq[1] == '/sensors':
        sensorUpdateStr = '<p>{}</p>'.format(sensors) ######################################################## Change to a dict input, somehow tie it to the top side functions
        writer.write(sensorUpdateStr)

    elif cmd_rq[1][:15] == '/led_set?state=':
        lightOut = strToLight(cmd_rq[1][15:])
        #pushLight(leds,[lightOut]*3)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")
    



    














html = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>PicoW | HomeStation</title></head>
<body> <h2>HomeStation</h2>
<p id="sensors">Getting sensor state...</p>
<p id="colour">{colour}</p>
{script}
</body>
</html>
"""

colour = '''
<label for="colorWell">LED Colour:</label>
<input type="color" value="#ff0000" id="colorWell">
'''

script = '''<script>
let colorWell;
const defaultColor = "#000000";
window.addEventListener("load", startup, false);
function startup() {
    colorWell = document.querySelector("#colorWell");
    colorWell.value = defaultColor;
    colorWell.addEventListener("input", updateFirst, false);
    colorWell.select();
}
function updateFirst(event) {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
        document.getElementById("state").innerHTML = this.responseText;
        }
    };
    xhttp.open("GET", "led_set?state=" + String(event.target.value).substr(1), true);
    xhttp.send();
}
setInterval(function() {
  getSensors();
}, 500);
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

