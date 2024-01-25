import re

# Class used to analyze data from the transmitter
class Analyzer():
    
    def __init__(self) -> None:
        self.NO_SIGNAL = 5
        self.RSSI_LOWER_THRESHOLD = 15
        self.RSSI_UPPER_THRESHOLD = 120
        self.SIGNIFICANT_RSSI_CHANGE = 5

        self.NO_AUDIO = 0
        self.AUDIO_LOWER_THRESHOLD = 10
        self.AUDIO_UPPER_THRESHOLD = 100
        self.SIGNIFICANT_AUDIO_CHANGE = 5

        self.rssi = 0
        self.last_rssi = 0
        self.last_rssi_code = 0
        self.rssi_change = 0
        self.if_count = False
        self.counter = 0
        self.count_no_signal = 0
        self.count_low_signal = 0
        self.count_correct_signal = 0

        self.audio_level = 0
        self.last_audio = 0
        self.audio_change = 0

        self.rds_code_set = False

        self.rds_pi = ''
        self.last_pi = ''
        self.last_pi_code = 0

        self.rds_ps = ''
        self.last_ps = ''
        self.last_ps_code = 0

        self.rds_rt = ''
        self.last_rt = ''
        self.last_rt_code = 0

        self.pi_pattern = re.compile("^[a-fA-F0-9]{4}$")
        self.ps_pattern = re.compile("^[a-z\s\\-]{8}$")

    # Method that extracts radio data from a given dictionary
    def data_from_dict(self, item):
        self.rssi = item['rssi']
        self.audio_level = item['audio']
        self.rds_pi = item['rds_pi']
        self.rds_ps = item['rds_ps']
        self.rds_rt = item['rds_rt']

    # Method that returns RSSI status code
    # code 00 -> strong signal
    # code 01 -> poor signal quality
    # code 10 -> no signal
    # code 11 -> left for future use
    def rssi_status(self):
        # check for significant change of rssi level
        delta_rssi = abs(self.last_rssi - self.rssi)
        self.rssi_change = delta_rssi > self.SIGNIFICANT_RSSI_CHANGE

        if self.if_count == False:
            # correct rssi level
            if self.rssi > self.RSSI_LOWER_THRESHOLD and self.rssi < self.RSSI_UPPER_THRESHOLD:
                rssi_status_code = 0
            # if low rssi detected start checking next values
            else:
                if self.rssi > self.RSSI_UPPER_THRESHOLD or self.rssi < self.NO_SIGNAL:
                    self.count_no_signal += 1
                elif self.rssi < self.RSSI_LOWER_THRESHOLD:
                    self.count_low_signal += 1
                
                self.rssi_status_code = self.last_rssi_code
                self.if_count = True
                self.counter += 1
        
        else:
            # count instances of correct, low and no signal values
            if self.rssi > self.RSSI_LOWER_THRESHOLD and self.rssi < self.RSSI_UPPER_THRESHOLD:
                self.count_correct_signal += 1
            elif self.rssi > self.RSSI_UPPER_THRESHOLD or self.rssi < self.NO_SIGNAL:
                self.count_no_signal += 1
            elif self.rssi < self.RSSI_LOWER_THRESHOLD:
                self.count_low_signal += 1

            self.rssi_status_code = self.last_rssi_code
            self.counter += 1

            # stop after checking 50 values and assign status code
            # based on number of instances of values in each range
            if self.counter == 50:
                instance_num = [self.count_no_signal * 1.4, self.count_low_signal * 1.2, self.count_correct_signal]
                self.rssi_status_code = 2 - instance_num.index(max(instance_num))

                self.if_count = False
                self.count_correct_signal = 0
                self.count_no_signal = 0
                self.count_low_signal = 0

        self.last_rssi_code = self.rssi_status_code
        self.last_rssi = self.rssi

        return rssi_status_code
        
    # Method that returns audio status code
    def audio_status(self):
        delta_audio = abs(self.last_audio - self.audio_level)
        self.audio_change = delta_audio > self.SIGNIFICANT_AUDIO_CHANGE

        # code 10 -> no audio (radio silence)
        if self.audio_level < self.NO_AUDIO:
            audio_status_code = 2
        # code 01 -> poor audio quality
        elif self.audio_level < self.AUDIO_LOWER_THRESHOLD:
            audio_status_code = 1
        # code 00 -> strong audio signal
        elif self.audio_level < self.AUDIO_UPPER_THRESHOLD:
            audio_status_code = 0
        # code 11 -> incorrect data (audio level exceeds the upper threshold)
        elif self.audio_level >= self.AUDIO_UPPER_THRESHOLD:
            audio_status_code = 3

        self.last_audio = self.audio_level

        return audio_status_code
    
    # Method that deletes unnecessary data records
    # if RDS doesn't change
    def filter_by_rds(self):
        if any((self.rds_pi != self.last_pi, self.rds_ps != self.last_ps, self.rds_rt != self.last_rt)):
            self.rds_code_set = False
            return 0, 0, 0
        elif not any((self.rssi_change, self.audio_change)):
            return None, None, None
        else:
            self.rds_code_set = True
            return self.last_pi_code, self.last_ps_code, self.last_rt_code
        
    # Method that returns RDS PI status code
    def rds_pi_status(self, is_rds):
        # code 11 -> no RDS
        if not is_rds:
            rds_pi_status_code = 3
        # code 01 -> empty field
        elif not self.rds_pi.strip():
            rds_pi_status_code = 1
        # code 10 -> incorrect PI (other format than 4 hexadecimal digits)
        elif not self.pi_pattern.match(self.rds_pi):
            rds_pi_status_code = 2
        # code 00 -> correct PI
        else:
            rds_pi_status_code = 0

        self.last_pi = self.rds_pi
        self.last_pi_code = rds_pi_status_code

        return rds_pi_status_code

    # Method that returns RDS PS status code
    def rds_ps_status(self, is_rds):
        # code 11 -> no RDS
        if not is_rds:
            rds_ps_status_code = 3
        # code 01 -> empty field
        elif not self.rds_ps.strip():
            rds_ps_status_code = 1
        # code 10 -> incorrect PS format
        elif not self.ps_pattern.match(self.rds_ps):
            rds_ps_status_code = 2
        # code 00 -> correct PS
        else:
            rds_ps_status_code = 0

        self.last_ps = self.rds_ps
        self.last_ps_code = rds_ps_status_code

        return rds_ps_status_code

    # Method that returns RDS RT status code
    def rds_rt_status(self, is_rds):
        # no RDS
        if not is_rds:
            rds_rt_status_code = 15
        # empty field
        elif not self.rds_rt.strip():
            rds_rt_status_code = 1
        # correct RT
        else:
            rds_rt_status_code = 0

        self.last_rt = self.rds_rt
        self.last_rt_code = rds_rt_status_code

        return rds_rt_status_code
        


    # Method that concatenates all status codes into one
    def status_code(self, rssi_status_code, audio_status_code, rds_pi_status_code, rds_ps_status_code, rds_rt_status_code):
        audio_status_code = audio_status_code << 2
        rds_pi_status_code = rds_pi_status_code << 4
        rds_ps_status_code = rds_ps_status_code << 6
        rds_rt_status_code = rds_rt_status_code << 8

        status_code = rssi_status_code + audio_status_code + rds_pi_status_code + rds_ps_status_code + rds_rt_status_code

        return status_code
        

    
if __name__ == "__main__":
        analyzer = Analyzer()
        is_rds = True

        # item = {"ts": 17034.7, "rssi": 9.1, "audio": 3, "rds_pi": 3233, "rds_ps": '--------', "rds_rt": 'radio text'}

        analyzer.data_from_dict(item)

        rssi_status_code = analyzer.rssi_status()
        audio_status_code = analyzer.audio_status()

        analyzer.filter_by_rds()

        if not analyzer.rds_code_set:
            rds_pi_status_code = analyzer.rds_pi_status(is_rds)
            rds_ps_status_code = analyzer.rds_ps_status(is_rds)
            rds_rt_status_code = analyzer.rds_rt_status(is_rds)

        status_code = analyzer.status_code(rssi_status_code, audio_status_code, rds_pi_status_code, rds_ps_status_code, rds_rt_status_code)
        item["status_code"] = status_code
        print(bin(status_code))
        print(status_code)