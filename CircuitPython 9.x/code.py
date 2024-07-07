# SPDX-FileCopyrightText: 2023 Phil Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
HAL 9000 demo project for Adafruit Prop Maker Feather RP2040 and "Massive
Arcade Button with LED - 100mm red." This simply monitors for button presses
and then randomly plays one WAV file from the CIRCUITPY filesystem.
No soldering required; using quick-connects, LED and button can be wired
to screw terminals on the Prop Maker Feather board.
NOTE: WAV FILES MUST BE 16-BIT. This will be fixed (allowing 8-bit WAVs if
desired) in CircuitPython 9.0.
"""

# pylint: disable=import-error
import os
import random
import time
import audiocore
import audiobusio
import board
import digitalio
import pwmio
from adafruit_debouncer import Debouncer
import adafruit_lis3dh
# import adafruit_debouncer

# HARDWARE SETUP -----------------------------------------------------------

# LED+ is wired to "Neo" pin on screw terminal header, LED- to GND.
# The LED inside the button is NOT a NeoPixel, just a normal passive LED,
# but that's okay here -- the "Neo" pin can also function like a simple
# 5V digital output or PWM pin.
led = pwmio.PWMOut(board.EXTERNAL_NEOPIXELS)
led.duty_cycle = 65535  # LED ON by default

# Button is wired to GND and "Btn" on screw terminal header:
button = digitalio.DigitalInOut(board.EXTERNAL_BUTTON)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP
switch = Debouncer(button)


# Enable power to audio amp, etc.
external_power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = digitalio.Direction.OUTPUT
external_power.value = True

# I2S audio out
audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)

# The onboard LIS3DH is initialized over I2C.
# In the loop, the LIS3DH will be able to affect the prop by detecting shake
i2c = board.I2C()
int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)
lis3dh.range = adafruit_lis3dh.RANGE_2_G

# PIR sensor connected to GPIO 26 (A0)
pir = digitalio.DigitalInOut(board.A0)
pir.direction = digitalio.Direction.INPUT

led1 = digitalio.DigitalInOut(board.A2)
led2 = digitalio.DigitalInOut(board.A3)
led3 = digitalio.DigitalInOut(board.D24)
led1.direction = digitalio.Direction.OUTPUT
led2.direction = digitalio.Direction.OUTPUT
led3.direction = digitalio.Direction.OUTPUT

# Find all Wave files in CIRCUITPY storage:
wavefilesold = [
    file
    for file in os.listdir("/sounds/old/")
    if (file.endswith(".wav") and not file.startswith("._"))
]
print("Audio files found old:", wavefilesold)

wavefilestitan = [
    file
    for file in os.listdir("/sounds/titan/")
    if (file.endswith(".wav") and not file.startswith("._"))
]
print("Audio files found titan:", wavefilestitan)

wavefilesfunny = [
    file
    for file in os.listdir("/sounds/funny/")
    if (file.endswith(".wav") and not file.startswith("._"))
]
print("Audio files found funny:", wavefilesfunny)

    
# FUNCTIONS ----------------------------------------------------------------


def play_file(filename):
    """Plays a WAV file in its entirety (function blocks until done)."""
    print("Playing", filename)
    led.duty_cycle = 65535
    time.sleep(0.1)
    led.duty_cycle = 0
    time.sleep(0.1)
    led.duty_cycle = 65535
    time.sleep(0.1)
    led.duty_cycle = 0
    time.sleep(0.1)
    with open(f"/sounds/{filename}", "rb") as file:
        audio.play(audiocore.WaveFile(file))
        # Randomly flicker the LED a bit while audio plays
        while audio.playing:
            led.duty_cycle = random.randint(5000, 30000)
            time.sleep(0.1)
    led.duty_cycle = 65535  # Back to full brightness


# MAIN LOOP ----------------------------------------------------------------


# Loop simply watches for a button press (button pin pulled to GND, thus
# False) and then plays a random WAV file. Because the WAV-playing function
# will take a few seconds, this doesn't even require button debouncing.
# while True:
#     if button.value is False:
#         play_file(random.choice(wavefiles))

# Constants for defining different press lengths
SHORT_PRESS_TIME = 0.5  # in seconds
LONG_PRESS_TIME = 4.5   # in seconds
FUNNY_PRESS_TIME = 5.4
# Variables to track button press state
button_pressed_time = None
button_released_time = None
ct = 490
while True:

    if lis3dh.shake(shake_threshold=10):
        print('Hey, put me down!!!')
        led1.value = True
        led2.value = True
        led3.value = True
        play_file("putmedown.wav")
        time.sleep(0.2)
        for i in range(10):
            led1.value = True
            led2.value = True
            led3.value = True
            time.sleep(0.2)
            led1.value = False
            led2.value = False
            led3.value = False
            time.sleep(0.2)
            
    if ct > 500:
        if pir.value: # If PIR detects movement
            print("I SEE YOU!")
            led1.value = True
            time.sleep(0.1)
            led2.value = True
            time.sleep(0.1)
            led3.value = True
            time.sleep(0.1)
            led1.value = False
            time.sleep(0.1)
            led2.value = False
            time.sleep(0.1)
            led3.value = False
            time.sleep(0.1)
            play_file("titan/"+random.choice(wavefilestitan))
            led1.value = True
            time.sleep(0.1)
            led2.value = True
            time.sleep(0.1)
            led3.value = True
            time.sleep(0.1)
            led1.value = False
            time.sleep(0.1)
            led2.value = False
            time.sleep(0.1)
            led3.value = False
            time.sleep(0.1)
            time.sleep(1) # Wait 5 seconds before looking for more movement
            
            print("Sensor active") # Let us know that the sensor is active
            ct = 0
        print(ct)
        
    switch.update()
    
    if switch.fell:
        print('Just pressed')
        button_press_time = time.monotonic()
    if switch.rose:
        print('Just released')
        # Button is released
        button_release_time = time.monotonic()
        press_duration = button_release_time - button_press_time
        print("press length: " + str(press_duration))
        if press_duration < SHORT_PRESS_TIME:
            # Short press action
            print(random.choice(wavefilesold))
            play_file("old/"+random.choice(wavefilesold))
            led1.value = True
            led2.value = True
            led3.value = True
            time.sleep(0.2)
            led1.value = False
            led2.value = False
            led3.value = False
            time.sleep(0.2)
        elif press_duration < LONG_PRESS_TIME:
            # Medium press action
            play_file("titan/"+random.choice(wavefilestitan))
            led1.value = True
            led2.value = True
            led3.value = True
            time.sleep(0.2)
            led1.value = False
            led2.value = False
            led3.value = False
            time.sleep(0.2)
            
        elif press_duration < FUNNY_PRESS_TIME:
            play_file("funny/"+random.choice(wavefilesfunny))
            
        else:
            # Long press action
            play_file("test/"+random.choice(wavefilesold))
            
    time.sleep(0.1)
    ct +=1
