from multiprocessing import Process, Queue
from TEF6686_driver import TEF6686
from paho.mqtt import client as mqtt_client

from time import sleep, time
import uuid
from analyze_data import Analyzer

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

    # Method to ensure that rds is active on given frequency
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
    def queue_radio_data(self, data_queue):
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
                self.rds_rt = rds_dict["RT"].rstrip()
            else:
                self.rds_pi = ""
                self.rds_ps = ""
                self.rds_rt = ""
            

            
            time_stamp = time()
            data_dict = {"ts": time_stamp, "rssi": self.rssi, "rds_pi": self.rds_pi, "rds_ps": self.rds_ps, "rds_rt": self.rds_rt}
            # print(data_dict)
            data_queue.put(data_dict)
            sleep(0.07)

    
    # Method for reading data from queue
    def analyze_radio_data(self, data_queue, analyzed_queue, analyzer):
        while True:
            item = data_queue.get()

            if item is None:
                break
            else:
                item['audio'] = 15.1
                analyzer.data_from_dict(item)

                rssi_status_code = analyzer.rssi_status()
                audio_status_code = analyzer.audio_status()

                rds_pi_status_code, rds_ps_status_code, rds_rt_status_code = analyzer.filter_by_rds()

                if rds_pi_status_code is None:
                    continue

                if not analyzer.rds_code_set:
                    rds_pi_status_code = analyzer.rds_pi_status(self.is_rds)
                    rds_ps_status_code = analyzer.rds_ps_status(self.is_rds)
                    rds_rt_status_code = analyzer.rds_rt_status(self.is_rds)

                status_code = analyzer.status_code(rssi_status_code, audio_status_code, rds_pi_status_code, rds_ps_status_code, rds_rt_status_code)
                item["code"] = status_code

                analyzed_queue.put(item)
    

    def send_analyzed_data(self, analyzed_queue):
        try:
            client = connect_mqtt()
        except:
            print("Nie połączono")
        else:
            client.loop_start()
            subscribe(client)
            while True:
                item = analyzed_queue.get()
                if item is None:
                    client.loop_stop()
                    break
                else:
                    msg = dict_to_csv(item)
                    # print(msg)
                    if publish(client, msg) != 0:
                        print("Failed to publish")
            



def dict_to_csv(data_dict):
    csv = f"{data_dict['ts']}, {data_dict['rssi']}, {data_dict['rds_pi']}, {data_dict['rds_ps']}, {data_dict['rds_rt']}, {data_dict['audio']}, {data_dict['code']}"
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


def publish(client: mqtt_client, msg):
    result = client.publish(topic, msg)
    status = result[0]
    return status


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(msg.payload.decode())
        try:
            radio_frequency = float(msg.payload.decode())
        except:
            print('Could not parse')
        else:
            if 87.5 < radio_frequency < 108:
                radio.init()
                radio.tune_to('FM', int(radio_frequency*100))
                radio.__PS_OFFSET__ = [False, False, False, False]
                radio.__PS_LIST__ = ['--','--', '--', '--']
            else:
                print('Bad frequency')

    client.subscribe(sub_topic)
    client.on_message = on_message


if __name__ == "__main__":
    client_id = hex(uuid.getnode())

    ################
    radio_frequency = 91.0 # [MHz] !!!!!!!!!
    # broker = '7.tcp.eu.ngrok.io'
    # port = 16091
    
    broker = '192.168.1.44'
    port = 1883

    topic = "sensor-data"
    sub_topic = "set-frequency"

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

    analyzer = Analyzer()

    queue_d = Queue()
    queue_a = Queue()
    queue_process = Process(target=radio.queue_radio_data, args=(queue_d,))
    analyze_process = Process(target=radio.analyze_radio_data, args=(queue_d, queue_a, analyzer,))
    publish_process = Process(target=radio.send_analyzed_data, args=(queue_a, ))

    # Setting frequency
    
    queue_process.start()
    analyze_process.start()
    publish_process.start()
    queue_process.join()
    analyze_process.join()
    publish_process.join()