from network import LoRa
import usocket
import time

# Please pick the region that matches where you are using the device

lora = LoRa(mode=LoRa.LORA, region=LoRa.EU868)
s = usocket.socket(usocket.AF_LORA, usocket.SOCK_RAW)
s.setblocking(False)
i = 0
while True:
    rcv_data = s.recv(80)
    print(rcv_data)
    if rcv_data == b'123456':
        print(rcv_data)
        s.send('Received')
        print('Received {}'.format(i))
        i = i+1
    time.sleep(1)