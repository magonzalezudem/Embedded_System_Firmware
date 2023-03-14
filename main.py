
import pycom
import time
import machine
import ujson
from machine import Pin
import lora_radio
import sensors
import _thread
import sensors
import gc
import socket
from bme280 import *
import dht22


global start_energy_measurement, power_list, toc, counter_ticks,voltage_list

def measure_energy(i2c):
    global start_energy_measurement, power_list, toc, voltage_list
    print('[INFO] Starting energy measurement thread...')

    while True:
        try:
            if start_energy_measurement == True:
                power_list = []
                voltage_list = []
                toc = []
                ina = sensors.energy(i2c)
                print('[INFO] Energy measurement started!')
                while start_energy_measurement:
                    tic = time.ticks_us()
                    power_list.append(ina.power()/1000)
                    #voltage_list.append(ina.voltage())
                    toc.append((time.ticks_us()-tic)/1e6)
                print('[INFO] Energy measurement stopped!')
        except Exception as e:
            print('[ERROR] Error measuring energy!: {}'.format(e))
            time.sleep(1)
        else:
            pass

def ticks(pin):
    global counter_ticks
    counter_ticks+=1
    print('[INFO] Tick counter: {}'.format(counter_ticks))
    with open('counter_ticks.txt','w') as f:
        f.write(str(counter_ticks))

if __name__ == '__main__':
    node_number = '1'
    print('[INFO] Starting script!')
    wdt = machine.WDT(timeout = 60000)
    wdt.feed()
    pycom.heartbeat(True)

    pycom.wifi_on_boot(False)

    counter_ticks = 0
    with open('counter_ticks.txt','r') as f:
        counter_ticks = int(f.read())

    rain_pin = Pin('P23', mode = Pin.IN, pull = Pin.PULL_UP)
    rain_pin.callback(Pin.IRQ_FALLING, ticks)
    i2c = machine.I2C(0, machine.I2C.MASTER, pins = ('P21','P22'), baudrate = 1000)
    try:
        bme280 = BME280(i2c=i2c)
    except:
        print('[ERROR] BMP280 not found! Power down and up and try again ..')

    th = dht22.DTH(Pin('P10', pull = Pin.PULL_UP, mode=Pin.OPEN_DRAIN),1)
    #th = dht22.DTH(Pin('P10'),1)

    #time.sleep(3)

    start_energy_measurement = False
    _thread.start_new_thread(measure_energy,(i2c,))

    with open('/flash/current_dr_iteration.txt','r') as f:
        iteration = int(f.read())
    with open('/flash/data_rate_variation.txt','r') as f:
        data_rate_variation = f.read()

    if iteration == -1:
        iteration = 0

    data_rate_variation = data_rate_variation.split(';')
    frequency_list =  data_rate_variation[0].split(',')
    frequency_list = list(map(lambda x: int(x),frequency_list))
    data_rate = data_rate_variation[1].split(',')
    data_rate = list(map(lambda x: int(x),data_rate))
    bit_length = data_rate_variation[2].split(',')
    bit_length = list(map(lambda x: int(x),bit_length))


    frequency = frequency_list[iteration]
    sf_datarate = data_rate[iteration]

    print('[INFO] Iteration: {}'.format(iteration))
    print('[INFO] Data rate: {}'.format(sf_datarate))
    print('[INFO] Bit length: {}'.format(bit_length[iteration]))
    print('[INFO] Frequency: {}'.format(frequency))

    with open('credentials.json','r') as f:
        credentials = ujson.loads(f.read())
    print('[INFO] Credentials: {}'.format(credentials[node_number]))


    frequencies = [903900000,904100000,904300000,904500000,904700000,904900000,905100000,905300000] #FB2
    lora = lora_radio.config_lora(method = 'ABP', frequency = frequency)
    s = lora_radio.join_network(lora,
                                method = 'ABP',
                                sf_datarate = sf_datarate,
                                node_number = node_number,
                                credentials = credentials)

    counter = 0

    sample_time = 15
    while True:
        wdt.feed()
        try:
            if frequency_list[iteration] == frequency:
                gc.collect()
                start = time.time()
                print('-'*100)
                #start_energy_measurement = True
                temperature, rh = sensors.thermohygrometer(th) # °C / %
                try:
                    temperature_1, press, dew_point = bme280.values # °C / hPa
                except:
                    print('[ERROR] BMP280 not discovered.')
                    press = 0
                port = UART(1, baudrate = 9600)
                pm2_5, pm10 = sensors.pm(port)
                #print('paso'*50)
                port.deinit()
                last_energy= 0              # Joules. It is multiplied by 1000 to preserve 3 decimal digits
                with open('last_energy.txt','r') as f:
                    last_energy = float(f.read())

                print('[INFO] Temperature: {} C, RH: {}%, Pressure: {} hPa, PM2.5: {} ug/m3, PM10: {} ug/m3, Last energy: {} J, Ticks: {}'.format(temperature,
                                                                                                                                        rh,
                                                                                                                                        press,
                                                                                                                                        pm2_5,
                                                                                                                                        pm10,
                                                                                                                                        last_energy,
                                                                                                                                        counter_ticks))

                #Frame configuration:
                # |C6:5bit|C5:16bit|C4:12bit|C3:12bit|C2:14bit|C1:10bit|C0:10bit|
                # C0: Temperature*10
                # C1: RH*10
                # C2: Barometric pressure*10
                # C3: PM2.5*10
                # C4: PM10*10
                # C5: Energy*1000
                # C6: Rain counter
                temperature_bin = sensors.binaryfy(temperature*10//1,10)
                #print('[INFO] Temperature bin: {}'.format(temperature_bin))
                rh_bin = sensors.binaryfy(rh*10//1,10)
                #print('[INFO] RH bin: {}'.format(rh_bin))
                press_bin = sensors.binaryfy(press*10//1, 14)
                #print('[INFO] Press bin: {}'.format(press_bin))
                pm2_5_bin = sensors.binaryfy(pm2_5*10//1,12)
                #print('[INFO] PM2.5 bin: {}'.format(pm2_5_bin))
                pm10_bin = sensors.binaryfy(pm10*10//1,12)
                #print('[INFO] PM10 bin: {}'.format(pm10_bin))
                last_energy_bin = sensors.binaryfy(last_energy*1000//1,16)
                #print('[INFO] Last energy bin: {}'.format(last_energy_bin))
                counter_ticks_bin = sensors.binaryfy(counter_ticks//1,5)

                binary_list = []
                binary_list.extend(temperature_bin)
                binary_list.extend(rh_bin)
                binary_list.extend(press_bin)
                binary_list.extend(pm2_5_bin)
                binary_list.extend(pm10_bin)
                binary_list.extend(last_energy_bin)
                binary_list.extend(counter_ticks_bin)
                # Ojoooo cambiar
                binary_list = sensors.dummyfy(binary_list,bit_length[iteration])
                
                #print('[INFO] Binary list: {}'.format(binary_list))
                
                coded_measurements = sensors.chunkfy(binary_list)
                #print('[INFO] Coded measurements: {}'.format(list(map(lambda x: hex(x),coded_measurements))))
                wdt.feed()
                # Ojooooo cambiar
                s.setsockopt(socket.SOL_LORA, socket.SO_DR, data_rate[iteration])
                #s.setsockopt(socket.SOL_LORA, socket.SO_DR, 0)
                """
                for i in range(0,72):
                    try:
                        lora.remove_channel(i)
                    except Exception as e:
                        print(e)
                print("+"*50)
                lora.add_channel(frequencies.index(frequency_list[iteration]),
                                 frequency = frequency_list[iteration],
                                 dr_min=0,
                                 dr_max=3)
                """

                tic = time.ticks_us()
                start_energy_measurement = True
                lora_radio.send(coded_measurements,lora,s)
                power = power_list
                execution_time = toc
                send_time = time.ticks_us()-tic
                start_energy_measurement = False
                wdt.feed()
                #Uncomment to log power and time in an internal file
                """
                power_string = ','.join(list(map(lambda x: str(x),power)))
                execution_string = ','.join(list(map(lambda x: str(x),execution_time)))

                with open('/flash/power.csv','w') as f:
                    f.write(execution_string+'\n'+power_string)
                """

                total_energy = []

                for i in range(len(power)):
                    total_energy.append(execution_time[i]*power[i])
                total_energy = sum(total_energy)
                with open('last_energy.txt','w') as f:
                    f.write(str(total_energy))

                print('[INFO] Transmission counter: {}'.format(iteration))
                print('[INFO] Frequency: {}'.format(frequency_list[iteration]))
                print('[INFO] SF: {}'.format(data_rate[iteration]))
                print('[INFO] Bit length: {}'.format(bit_length[iteration]))
                print('[INFO] Total energy: {} Joules'.format(total_energy))
                print('[INFO] Total time: {} us'.format(send_time))
                print('[INFO] LoRaWAN stats: {}'.format(lora.stats()))

                if iteration < len(data_rate) -1:
                    iteration += 1
                else:
                    iteration = 0

                with open('/flash/current_dr_iteration.txt','w') as f:
                    f.write(str(iteration))

                counter_ticks = 0
                with open('counter_ticks.txt','w') as f:
                    f.write('0')

                if iteration == 0:
                    print('[INFO] All the iterations with DR = 0 were performed. Restarting...')
                    with open('/flash/current_dr_iteration.txt','w') as f:
                        f.write(str(iteration-1))
                    machine.reset()

                stop = time.time() - start
                print("[INFO] Execution time: {}".format(stop))
                if (sample_time-stop)>0:
                    time.sleep(sample_time-stop)


            else:
                print('[INFO] All the iterations with DR = {} were performed. Restarting...'.format(sf_datarate))
                with open('/flash/current_dr_iteration','w') as f:
                    f.write(str(iteration-1))
                machine.reset()


        except Exception as e:
            exception = '{}'.format(e)
            print('[ERROR] General exception: {}'.format(e))
            if exception == 'I2C bus error':
                machine.reset()
            time.sleep(10)
            machine.reset()
