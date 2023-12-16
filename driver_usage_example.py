from TEF6686_driver import TEF6686
import time

#-------------- NEW TUNER INSTANCE ----------------

tuner = TEF6686('RPi')

#------- INIT TUNER MODULE AND SETTINGS -----------

tuner.init()
tuner.set_volume_gain(10)

tuner.start_oscillator()					# oscillator can be 4 or 9.216 MHz

tuner.load_settings()					# settings that produce good quality and high sensitivity

tuner.check_tuner_status() 				# should now return "Radio standby" or "ACTIVE" state

#----------------   USE TUNER ---------------------

tuner.tune_to('FM',10750)
RDS_status = False
RSSI = 0
STEREO = False
IF = 0
while not RDS_status:
    RSSI, STEREO, RDS_status, IF = tuner.get_signal_info(mode="full")
while True:
    print(list(tuner.get_RDS_data(pause_time=0, repeat=False)))
    time.sleep(0.5)
