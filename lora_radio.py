import time
from network import LoRa
import ubinascii
import uos
import machine
import socket
import struct
from network import WLAN

def activate_ftp():
    wlan = WLAN(mode=WLAN.STA)
    wlan.connect(ssid='ELIANAI', auth=(WLAN.WPA2, '71262387'))
    while not wlan.isconnected():
        pass
    print('[INFO] WLAN settings: {}'.format(wlan.ifconfig()))
    return wlan


def config_lora(method = 'ABP',frequency = 905300000):
    print('[INFO] Configuring LoRaWAN radio...')
    lora = LoRa(mode=LoRa.LORAWAN)
    print('[INFO] Configuring LoRaWAN settings...')

    lora.init(mode=LoRa.LORAWAN,
                region=LoRa.US915,
                tx_power = 10, # 30-2*TX
                bandwidth = LoRa.BW_125KHZ,
                sf = 8,
                preamble = 8,
                coding_rate = LoRa.CODING_4_5,
                adr = False)
    lora.nvram_restore()
    #print('[INFO] TX power: {}'.format(lora.tx_power()))

    # create an OTAA authentication parameters
    print('[INFO] Configuring LoRaWAN radio...')

    if method == 'OTAA':
        for i in range(0,72):
            lora.remove_channel(i)
        print('[INFO] Configuring LoRaWAN channels...')
        frequencies = [903900000,904100000,904300000,904500000,904700000,904900000,905100000,905300000] #FB2
        lora.add_channel(frequencies.index(frequency), frequency = frequency, dr_min=0, dr_max=3) # OK

    if method == 'ABP':
        for i in range(0,8):
            lora.remove_channel(i)
        for i in range(16,65):
            lora.remove_channel(i)
        for i in range(66,72):
            lora.remove_channel(i)

    print('[INFO] LoRaWAN radio configured!')

    return lora

def join_network(lora, method = 'OTAA', sf_datarate = 0, node_number= 0, credentials = {}):

    """
    try:
        lora.nvram_restore()
    except Exception as e:
        print('[ERROR] No saved configuration for LoRa Radio: {}'.format(e))
    """

    if method == 'OTAA':
        # join a network using OTAA (Over the Air Activation)

        dev_eui = ubinascii.unhexlify(credentials[node_number]["OTAA"]["dev_eui"])
        app_eui = ubinascii.unhexlify(credentials[node_number]["OTAA"]["app_eui"])
        app_key = ubinascii.unhexlify(credentials[node_number]["OTAA"]["app_key"])

        print('[INFO] Joining LoRaWAN network by using OTAA...')
        lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)

        # wait until the module has joined the network
        counter = 0
        delay = 2.5
        max_count = int(12.5/delay)
        while not lora.has_joined():
            time.sleep(delay)
            print('[INFO] Connecting to LoRa GW... Time elapsed: ',delay*counter, 'seconds.')
            counter+=1
            if counter == max_count:
                print('[ERROR] LoRa network not reached! Restarting...')
                machine.reset()

    if method == 'ABP':
        # create an ABP authentication parameters
        dev_eui = ubinascii.unhexlify(credentials[node_number]["ABP"]["dev_eui"])
        dev_addr = struct.unpack(">l", ubinascii.unhexlify(credentials[node_number]["ABP"]["dev_addr"]))[0]
        app_swkey = ubinascii.unhexlify(credentials[node_number]["ABP"]["app_swkey"])
        nwk_swkey = ubinascii.unhexlify(credentials[node_number]["ABP"]["nwk_swkey"])
        

        # join a network using ABP (Authentication by Personalization)
        lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))
        print('Joining LoRaWAN network by using ABP...')
        #time.sleep(5)


    # create a LoRa socket
    print('[INFO] Creating LoRaWAN socket...')
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    # set the LoRaWAN data rate
    print('[INFO] Setting LoRaWAN datarate...')
    # Ojo camibiar
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, sf_datarate)
    #s.setsockopt(socket.SOL_LORA, socket.SO_DR, 0)
    #lora.tx_power(10)
    # 0: SF-10 - max length 11 bytes
    # 1: SF-9 - max length 53 bytes
    # 2: SF-8 - max length 125 bytes
    # 3: SF-7 - max length 242 bytes
    print('[INFO] LoRaWAN socket created!')


    return s

def send(data, lora, s):
    print('[INFO] Sending information...')

    s.setblocking(True)
    s.send(bytes(data))
    s.setblocking(False)

    print('[INFO] Data sent!')
    lora.nvram_save()

if __name__ == '__main__':
    lora = config_lora()
    s = join_network(lora)
    coded_measurements = [uos.urandom(1)[0] for i in range(10)]
    send(coded_measurements,lora,s)
