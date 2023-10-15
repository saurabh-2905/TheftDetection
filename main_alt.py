### Import Pysense libraries
from pycoproc_2 import Pycoproc
import pycom
import _thread
from network import LoRa
import socket
import utime
import machine
from machine import Timer

from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
### Import of a file containing functions for connecting to TTN.
import LoRaConnection

from varlogger import VarLogger as logger



### put all the functionality in different functions to be able to run in multiple threads, use a class with methods as '@classmethod' so that we can pass class itslef as an argument and dont need to make an instance to be able to use class variables
def main():
    try:
        print('thread id1:', _thread.get_ident())
        ### init pyproc for reading data
        py = Pycoproc()

        ### Turn off the PyCom "Heartbeat" - the constant blinking of the indicator LED
        pycom.heartbeat(False)

        ### Set indicator LED to blue in order to signify that a successful connection has been established and that the sensor readout is now starting
        pycom.rgbled(0x00008B) # blue
        utime.sleep(2)

        ### Below is the initialisation of all hardware components that are connected to the LoPy4
        si = SI7006A20(py)

        ### The adx and itg variables hold instances of classes that represent the ADXL345 accelerometer and ITG3200 gyroscope respectively.
        li = LIS2HH12(py)

        ### The tenMinutes and thirtyMinutes variables hold values of ten and thirty minutes in seconds, respectively.
        tenMinutes = 1 * 60
        thirtyMinutes = 3 * tenMinutes


        ### This is the main part of the programme which runs in an infinite loop until the device is stopped or an error occurs. Indicator set to green to show arrival at main loop
        pycom.rgbled(0x008B00) # green
        control.init_timer0() ### time in seconds
        i=0
        while i <20:
            ### sense the data
            acceleration = sense(li)
            utime.sleep(2)
            ### send the data via lora communication
            #lock.acquire()
            ### push data to control and signal the communication thread to tx the data
            control.updatedata(acceleration)

            ### transmit data periodically
            print('timer status:', control.read_timer0())
            if control.read_timer0() > 5000: ### in ms
                loracom()
                control.reset_timer0() ### time in seconds
            #lock.release()
            i+=1

        ### Turn on the PyCom "Heartbeat" - the constant blinking of the indicator LED
        pycom.heartbeat(True)
    except KeyboardInterrupt:
        _thread.exit()



def sense(li):
    global start_time
    ### The acceleration info is requested from the sensor at every loop
    acceleration = li.acceleration()
    print("Acceleration: " + str(acceleration), utime.ticks_diff(utime.ticks_ms(), start_time))
    xAcceleration = acceleration[0]
    yAcceleration = acceleration[1]
    zAcceleration = acceleration[0]

    return acceleration
    

def loracom():
    global start_time
    print('thread 2:', _thread.get_ident())
    lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868)   
    
    print('lora:', utime.ticks_diff(utime.ticks_ms(), start_time))
    #lock.acquire()
    data = str(control.readdata()[0])
    print(data)
    #lock.release()
    ### create a LoRa socket
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    ### make the socket blocking
    ###(waits for the data to be sent and for the 2 receive windows to expire)
    s.setblocking(False)

    ### send some data
    s.send(data)
    print('Data sent')

    ### make the socket non-blocking
    ### (because if there's no data received it will block forever...)
    s.close()
    utime.sleep(2)

class control:
    '''
    this class is used to communicate between threads and manage shared resources
    @classmethod: allows to pass the class as the argument, inturn allows to update the attributes of the class without creating the instance of the class
    '''
    sensor_data = []
    tx_flag = False   ### to indidcate transmission if loracom runs in seperate thread
    timer0_done = False ### flag to indicate timer had completed count to trigger other processes
    timer0 = Timer.Chrono()


    @classmethod
    def updatedata(cls, data):
        ### update the sensor data in shared variable
        cls.sensor_data = [data]
    
    @classmethod
    def readdata(cls):
        ### read the sensor data from shared variable
        return cls.sensor_data
    
    @classmethod
    def init_timer0(cls):
        ### initialize the timer object with duration equal to time
        #cls.timer0.init(Timer.ONE_SHOT, time, cls.sett0)
        #timer0 = Timer.Alarm(cls.sett0, time, periodic=False)  ### time in seconds, as no arguments passed to callback it passes the object itself
        cls.timer0.start()
        print(cls.timer0.read_ms())  ### check
    
    @classmethod
    def read_timer0(cls):
        ### get the count of timer0 to check if it has completed counting (milliseconds)
        return cls.timer0.read_ms()
    
    @classmethod
    def reset_timer0(cls):
        ### reset chrono timer
        cls.timer0.reset()
    
    @classmethod
    def stop_timer0(cls):
        ### stop chrono timer
        cls.timer0.stop()



try:
    ### initialize it outside the scope of any function to allow access to all the code
    start_time = utime.ticks_ms()

    main_thread = _thread.start_new_thread(main, ())
    #comm_thread = _thread.start_new_thread(loracom, ())

except RuntimeError as e:
    print('Error message:', e)