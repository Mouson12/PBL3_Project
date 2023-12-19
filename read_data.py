from multiprocessing import Process, Queue
from TEF6686_driver import TEF6686
from paho.mqtt import client as mqtt_client

from time import sleep, time
from datetime import datetime
import logging
import uuid


class Radio(TEF6686):
    def __init__(self, DEVICE_ID, DEVICE = 'RPi', I2C_SDA = None, I2C_SCL = None, I2C_HW_ESP = -1) -> None:
        super().__init__(DEVICE, I2C_SDA, I2C_SCL, I2C_HW_ESP)
        self.id = DEVICE_ID
        self.rssi = 0
        self.is_stereo = False
        self.is_rds = False
        self.if_band = 0
        self.rds_pi = '----'
        self.rds_ps = '--------'
        self.rds_rt = '--------------------------------'

    # Method to ensure, that rds is active on given frequency
    def start_rds(self, RDS_TIMEOUT: int = 10):
        wait_time = RDS_TIMEOUT * 10
        count = 0
        print("Waiting for RDS")
        while not self.is_rds:
            if count < wait_time:
                self.rssi, self.is_stereo, self.is_rds, self.if_band \
                    = self.get_signal_info(mode="full")
                self.rssi = round(self.rssi, 1)
                print(self.rssi)
                print(self.if_band)
                count += 1
                sleep(0.1)
            else:
                print("RDS not available")
                return None
        print("RDS available")
        return None

    # Method for writing rssi, ps rds, rt rds to queue
    def write_radio_data(self, data_queue):
        dict_list = []
        while True:
            self.rssi, self.is_stereo, self.is_rds, self.if_band \
                = self.get_signal_info(mode="full")
            self.rssi = round(self.rssi, 1)

            if self.is_rds:
                for rds_dict in radio.get_RDS_data(pause_time=0, repeat=False):
                    dict_list.append(rds_dict)                
            
            if len(dict_list) > 0:
                rds_dict = dict_list[-1]
                self.rds_pi = rds_dict["PI"]  
                self.rds_ps = rds_dict["PS"]
                self.rds_rt = rds_dict["RT"]
            else:
                self.rds_pi = ""
                self.rds_ps = ""
                self.rds_rt = ""
            

            
            time_stamp = time()
            data_dict = {"ts": time_stamp, "rssi": self.rssi, "rds_pi": self.rds_pi, "rds_ps": self.rds_ps, "rds_rt": self.rds_rt}
            # print(self.is_rds)
            # print(data_dict)
            data_queue.put(data_dict)
            sleep(0.07)

    
    # Method for reading data from queue
    def read_radio_data(self, data_queue, client):
        while True:
            item = data_queue.get()
            
            if item is None:
                break
            else:
                msg = dict_to_csv(item)
                publish(client, msg)
                print(item)


def dict_to_csv(data_dict):
    csv = f"{data_dict['ts']}, {data_dict['rssi']}, {data_dict['rds_pi']}, {data_dict['rds_ps']}, {data_dict['rds_rt']}"
    return csv
    

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client, msg):
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")



def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()


if __name__ == "__main__":
    client_id = hex(uuid.getnode())

    ################
    radio_frequency = 98.8 # [MHz] !!!!!!!!!
    broker = '192.168.114.43'
    port = 1883
    topic = "sensor-data"
    ################

    # Starting radio tuner 
    
    print (client_id)
    radio = Radio(client_id)
    radio.init()
    radio.set_volume_gain(10)
    radio.start_oscillator()
    radio.load_settings()
    radio.check_tuner_status()

    radio.tune_to('FM', int(radio_frequency*100)) 
    """
    Start client
    """

    client = connect_mqtt()

    queue_d = Queue()
    write_process = Process(target=radio.write_radio_data, args=(queue_d,))
    read_process = Process(target=radio.read_radio_data, args=(queue_d, client,))

    # Setting frequency
    
    write_process.start()
    read_process.start()
    write_process.join()
    read_process.join()