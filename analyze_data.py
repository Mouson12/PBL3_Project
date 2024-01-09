# Class used to analyze data from the transmitter
class Analyzer():
    
    def __init__(self) -> None:
        self.NO_SIGNAL = 0
        self.RSSI_THRESHOLD = 10
        self.SIGNIFICANT_RSSI_CHANGE = 5

        self.NO_AUDIO = 0
        self.AUDIO_THRESHOLD = 10
        self.SIGNIFICANT_AUDIO_CHANGE = 5

        self.rssi = 0
        self.last_rssi = 0
        self.rssi_change = 0

        self.audio_level = 0
        self.last_audio = 0
        self.audio_change = 0

        self.rds_pi = ''
        self.last_pi = ''
        self.last_pi_code = 0

        self.rds_ps = ''
        self.last_ps = ''
        self.last_ps_code = 0

        self.rds_rt = ''
        self.last_rt = ''
        self.last_rt_code = 0

    # Method that extracts radio data from a given dictionary
    def data_from_dict(self, item):
        self.rssi = item['rssi']
        self.audio_level = item['audio']
        self.rds_pi = item['rds_pi']
        self.rds_ps = item['rds_ps']
        self.rds_rt = item['rds_rt']

    # Method that returns RSSI status code
    def rssi_status(self):
        delta_rssi = abs(self.last_rssi - self.rssi)
        self.rssi_change = delta_rssi > self.SIGNIFICANT_RSSI_CHANGE

        if self.rssi >= self.RSSI_THRESHOLD:
            rssi_status_code = 0
        elif self.rssi == self.NO_SIGNAL:
            rssi_status_code = 1
        elif self.rssi < self.RSSI_THRESHOLD:
            rssi_status_code = 2
        else:
            rssi_status_code = 3

        self.last_rssi = self.rssi

        return rssi_status_code
        
    # Method that returns audio status code
    def audio_status(self):
        delta_audio = abs(self.last_audio - self.audio_level)
        self.audio_change = delta_audio > self.SIGNIFICANT_AUDIO_CHANGE

        if self.audio_level >= self.AUDIO_THRESHOLD:
            audio_status_code = 0
        elif self.audio_level == self.NO_AUDIO:
            audio_status_code = 1
        elif self.audio_level < self.AUDIO_THRESHOLD:
            audio_status_code = 2
        else:
            audio_status_code = 3

        self.last_audio = self.audio_level

        return audio_status_code
    
    # Method that deletes unnecessary data records
    # if RDS doesn't change
    def filter_by_rds(self):
        if any(self.rds_pi != self.last_pi, self.rds_ps != self.last_ps, self.rds_rt != self.last_rt):
            pass
        elif not any(self.rssi_change, self.audio_change):
            return None
        else:
            self.rds_pi_status_code = self.last_pi_code
            self.rds_ps_status_code = self.last_ps_code
            self.rds_rt_status_code = self.last_rt_code
        
    # Method that returns RDS PI status code
    def rds_pi_status(self, is_rds):
        # no RDS
        if not is_rds:
            rds_pi_status_code = 3
        # empty field
        elif not self.rds_pi.strip():
            rds_pi_status_code = 1
        # wrong data type (not a string)
        elif not isinstance(self.rds_pi, str):
            rds_pi_status_code = 2
        # correct PI
        else:
            rds_pi_status_code = 0

        self.last_pi = self.rds_pi
        self.last_pi_code = rds_pi_status_code

        return rds_pi_status_code

    # Method that returns RDS PS status code
    def rds_ps_status(self, is_rds):
        # no RDS
        if not is_rds:
            rds_ps_status_code = 3
        # empty field
        elif not self.rds_ps.strip():
            rds_ps_status_code = 1
        # wrong data type (not a string)
        elif not isinstance(self.rds_ps, str):
            rds_ps_status_code = 2
        # correct PS
        else:
            rds_ps_status_code = 0

        self.last_ps = self.rds_ps
        self.last_ps_code = rds_ps_status_code

        return rds_ps_status_code

    # Method that returns RDS RT status code
    # used status codes: 0, 1, 2, 15
    # status codes 3-14 left for future use
    def rds_rt_status(self, is_rds):
        # no RDS
        if not is_rds:
            rds_rt_status_code = 15
        # empty field
        elif not self.rds_rt.strip():
            rds_rt_status_code = 1
        # wrong data type (not a string)
        elif not isinstance(self.rds_rt, str):
            rds_rt_status_code = 2
        # correct RT
        else:
            rds_rt_status_code = 0

        self.last_rt = self.rds_rt
        self.last_rt_code = rds_rt_status_code

        return rds_rt_status_code
        


    # Method that concatenates all status codes into one
    def status_code(self, rssi_status_code, audio_status_code, rds_pi_status_code, rds_ps_status_code, rds_rt_status_code):
        print(rssi_status_code)
        print(audio_status_code)
        print(rds_pi_status_code)
        print(rds_ps_status_code)
        print(rds_rt_status_code)
        audio_status_code = audio_status_code << 2
        print(bin(audio_status_code))
        rds_pi_status_code = rds_pi_status_code << 4
        print(bin(rds_pi_status_code))
        rds_ps_status_code = rds_ps_status_code << 6
        print(bin(rds_ps_status_code))
        rds_rt_status_code = rds_rt_status_code << 8
        print(bin(rds_rt_status_code))


        status_code = rssi_status_code + audio_status_code + rds_pi_status_code + rds_ps_status_code + rds_rt_status_code

        return status_code
        

    
if __name__ == "__main__":
        analyzer = Analyzer()
        is_rds = True

        item = {"ts": 17034.7, "rssi": 9.1, "audio": 3, "rds_pi": 3233, "rds_ps": '--------', "rds_rt": 'radio text'}

        analyzer.data_from_dict(item)

        rssi_status_code = analyzer.rssi_status()
        audio_status_code = analyzer.audio_status()
        rds_pi_status_code = analyzer.rds_pi_status(is_rds)
        rds_ps_status_code = analyzer.rds_ps_status(is_rds)
        rds_rt_status_code = analyzer.rds_rt_status(is_rds)

        status_code = analyzer.status_code(rssi_status_code, audio_status_code, rds_pi_status_code, rds_ps_status_code, rds_rt_status_code)
        print(bin(status_code))
        print(status_code)