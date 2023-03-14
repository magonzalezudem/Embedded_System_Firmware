import dht22
from machine import Pin
import time
import ina219
from machine import I2C, Pin
from ina219 import INA219
from bme280 import *
from machine import UART

def decode_bytes(number):
    number = int(number*10)
    number_high = (number & 0b1111111100000000)>>8
    number_low = number & 0b0000000011111111
    return [number_high,number_low]

def serialize_measurements(measurements):
    """
    measurements = [decode_bytes(element) for element in measurements]
    coded_measurements = []
    for item in measurements:
        coded_measurements.extend(item)
    """
    return coded_measurements

def binaryfy(number, digits):
    if number<0:
        number = 0
    list_number = []
    while number >1:
        list_number.append((number%2)//1)
        number = number //2
    list_number.append(number)
    list_number.extend([0]*(digits-len(list_number)))
    list_number = list(map(lambda x: int(x),list_number))
    return list_number

def decimalify(list_number):
    acum = 0
    for i in range(len(list_number)):
        acum += list_number[i]*(2**i)
    return acum

def bytefy(number):
    mask = 0x0000000000000000FF
    list_hexa = []
    for i in range(9):
        list_hexa.append(number & mask)
        number = number>>8
    return list_hexa

def thermohygrometer(th):
    try:
        temperature = 0
        humidity = 0
        retry = 0
        while temperature == 0 and humidity == 0 and retry<10:
            result = th.read()
            temperature = result.temperature
            humidity = result.humidity
            print("[INFO] Trial: {},  Temperature: {}, RH: {}".format(retry,temperature, humidity))
            retry+=1
            time.sleep(0.1)

        if result.is_valid():
            temperature = result.temperature/1.0
            rh = result.humidity/1.0
            print('[INFO] Thermohygrometer information retrieved successfully')
            return temperature, rh
        else:
            print('[ERROR] Thermohygrometer information not retrieved.')
            return 0,0
    except Exception as e:
        print('[ERROR] Thermohygrometer routine error: {}'.format(e))
        return -100,-100

def energy(i2c):
    SHUNT_OHMS = 0.1
    ina = INA219(SHUNT_OHMS, i2c)
    ina.configure()
    return ina



def dummyfy(list_number, bits):
    list_number.extend([1]*(bits-len(list_number)))
    return list_number

def chunkfy(list_number):
    chunks_number = len(list_number)//8
    chunks_list = []
    for i in range(chunks_number):
        temp = list_number[i*8:i*8+8]
        chunks_list.append(temp)
    list_hexa = []
    for i in range(len(chunks_list)):
        list_hexa.append(decimalify(chunks_list[i]))

    #list_hexa.reverse()
    return list_hexa

def pm(uart):
    try:
        counter = 0
        timeout = 5
        while uart.any() == 0:
            time.sleep(1)
            counter+=1
            if counter == timeout:
                print('[ERROR] No PM2.5 data retrieved!')
                return 0,0
        data = list(uart.read())
        #print('[INFO] PM2.5 frame: {}'.format(data))
        pm2_5 = int(data[6]*256 + data[7])
        pm10 = int(data[8]*256 + data[9])
    except Exception as e:
        print('[ERROR] Exception in PM2.5 routine: {}'.format(e))
        return 0,0

    return pm2_5, pm10

def pm_1(port, verbose = True):
    #disable auto send
    port.write(bytes([0x68,0x01,0x20,0x77]))
    time.sleep(0.1)
    response = list(map(lambda x: hex(x),list(port.read())))
    if verbose:
        print("[INFO]: Stop auto send command answer: {}".format(response))
    #start measurement
    port.write(bytes([0x68,0x01,0x01,0x96]))
    time.sleep(0.1)
    response = list(map(lambda x: hex(x),list(port.read())))
    if verbose:
        print("[INFO]:Start measurement command answer: {}".format(response))
    #read measurements
    port.write(bytes([0x68,0x01,0x04,0x93]))
    time.sleep(0.1)
    data = list(port.read())
    if verbose:
        print("[INFO]:Read particles answer: {}".format(data))
    pm2_5 = int(data[3]*256 + data[4])
    pm10 = int(data[5]*256 + data[6])

    return pm2_5, pm10





if __name__ == '__main__':
    th = dht22.DTH(Pin('P10', pull = Pin.PULL_UP, mode=Pin.OPEN_DRAIN),1)
    counter = 0
    while True:
        temperature,humidity = thermohygrometer(th)
        time.sleep(0.1)
        """
        temperature = 0
        humidity = 0
        retry = 0
        while temperature == 0 and humidity == 0 and retry<5:
            result = th.read()
            temperature = result.temperature
            humidity = result.humidity
            print(retry, temperature,humidity)
            retry+=1

        counter+=1
        time.sleep(0.05)
        """
    #temperature, rh = thermohygrometer()
    #print(temperature, rh)
    #energy()
    # from machine import I2C
    # i2c = I2C(0, I2C.MASTER, pins = ('P21','P22'), baudrate = 1000)
    # bme280 = BME280(i2c=i2c)
    # while True:
    #     print(bme280.values)
    #     time.sleep(1)
    """
    port = UART(1, baudrate = 9600)
    while True:
        pm2_5, pm10 = pm(port)
        print(pm2_5,pm10)
    """


from machine import I2C
i2c = I2C(0, I2C.MASTER, pins = ('P21','P22'), baudrate = 1000)
i2c.scan()
