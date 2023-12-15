from TEF6686_tuner import TEF6686

#-------------- NEW TUNER INSTANCE ----------------

tuner = TEF6686('RPi')

#------- INIT TUNER MODULE AND SETTINGS -----------

tuner.init()					# upload patch for DSP

tuner.start_oscillator()					# oscillator can be 4 or 9.216 MHz

tuner.load_settings()					# settings that produce good quality and high sensitivity

tuner.check_tuner_status() 				# should now return "Radio standby" or "ACTIVE" state

#----------------   USE TUNER ---------------------

tuner.set_volume_gain(0)				# volume gain: -599 to 240 (div. by 10: gain in dB!)

tuner.tune_to('FM',9880)

print(tuner.get_signal_info(mode="full", dbg=True))					# returns info about tuned signal: strength in dBµV, stereo (true/false), RDS available (true/false)

tuner.get_RDS_data()					# rudimentary implementation to read RDS PS, PTY, TP
