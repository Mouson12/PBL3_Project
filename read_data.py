from multiprocessing import Process, Queue
from TEF6686_driver import TEF6686
from time import sleep
from datetime import datetime
import logging

class Radio(TEF6686):
    def __init__(self, DEVICE = 'RPi', I2C_SDA = None, I2C_SCL = None, I2C_HW_ESP = -1) -> None:
        super().__init__(DEVICE, I2C_SDA, I2C_SCL, I2C_HW_ESP)
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
                    = radio.get_signal_info(mode="full")
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
        data_list = []
        while True:
            self.rssi, self.is_stereo, self.is_rds, self.if_band \
                = radio.get_signal_info(mode="full")
            self.rssi = round(self.rssi, 1)

            if not self.is_rds:
                data_queue.put(None)
                break

            for rds_dict in radio.get_RDS_data(pause_time=0, repeat=False):
                dict_list.append(rds_dict)
            
            if len(dict_list) > 0:
                rds_dict = dict_list[-1]
                self.rds_pi = rds_dict["PI"]  
                self.rds_ps = rds_dict["PS"]
                self.rds_rt = rds_dict["RT"]
            
            data_list = [self.rssi, self.rds_ps, self.rds_rt]
            data_queue.put(data_list)
            sleep(0.07)

    
    # Method for reading data from queue
    def read_radio_data(self, data_queue):
        while True:
            item = data_queue.get()
            
            if item is None:
                break
            else:
                print(item)



if __name__ == "__main__":
    ################
    radio_frequency = 91 # [MHz] !!!!!!!!!
    ################

    # Starting radio tuner 
    radio = Radio()
    radio.init()
    radio.set_volume_gain(10)
    radio.start_oscillator()
    radio.load_settings()
    radio.check_tuner_status()

    # Setting frequency
    radio.tune_to('FM', int(radio_frequency*100)) 

    # Waiting for rds
    radio.start_rds()

    # Starting processes
    queue = Queue()
    write_process = Process(target=radio.write_radio_data, args=(queue,))
    read_process = Process(target=radio.read_radio_data, args=(queue,))
    write_process.start()
    read_process.start()
    write_process.join()
    read_process.join()