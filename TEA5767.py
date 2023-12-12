"""
Micropython library from:
https://github.com/alankrantas/micropython-TEA5767
"""

import time
import busio
import board

class Radio:
    """
   TEA5767 FM radio driver class. 
   Initialize:
        radio = TEA5767.Radio(i2c, [addr=0x60, freq=106.7, band='US', stereo=True,
                                    soft_mute=True, noise_cancel=True, high_cut=True])
    """

    FREQ_RANGE_US = (87.5, 108.0)
    FREQ_RANGE_JP = (76.0, 91.0)
    ADC = (0, 5, 7, 10)
    ADC_BIT = (0, 1, 2, 3)

    __slot__ = ['_i2c', '_address', 'frequency', 'band_limits', 'standby_mode', 'mute_mode', 'soft_mute_mode',
                'search_mode', 'search_direction', 'search_adc_level', 'stereo_mode', 'stereo_noise_cancelling_mode',
                'high_cut_mode', 'is_ready', 'is_stereo', 'signal_adc_level']

    def __init__(self, addr=0x60, freq=0.0, band='US', stereo=True,
                            soft_mute=True, noise_cancel=True, high_cut=True):
        self._i2c = busio.I2C(board.SCL, board.SDA) # I2C from busio
        self._address = addr
        self.frequency = freq
        self.band_limits = band
        self.standby_mode = False
        self.mute_mode = False
        self.soft_mute_mode = soft_mute
        self.search_mode = False
        self.search_direction = 1
        self.search_adc_level = 7
        self.stereo_mode = stereo
        self.stereo_noise_cancelling_mode = noise_cancel
        self.high_cut_mode = high_cut
        self.is_ready = False
        self.is_stereo = False
        self.signal_adc_level = 0
        self.update()
        time.sleep(0.1)

    def set_frequency(self, freq):
        self.frequency = freq
        self.update()

    def change_freqency(self, change):
        self.frequency += change
        self.search_direction = 1 if change >= 0 else 0
        self.update()

    def search(self, mode, dir=1, adc=7):
        self.search_mode = mode
        self.search_direction = dir
        self.search_adc_level = adc if adc in Radio.ADC else 7
        self.update()

    def mute(self, mode):
        self.mute_mode = mode
        self.update()

    def standby(self, mode):
        self.standby_mode = mode
        self.update()

    def read(self):
        buf = [0]*5
        self._i2c.readfrom_into(self._address, buf) # reading whole buffer

        for i in range(5):
            print(hex(buf[i]))

        freqB = int((buf[0] & 0x3f) << 8 | buf[1])
        self.frequency = round((freqB * 32768 / 4 - 225000) / 1000000, 1)
        self.is_ready = int(buf[0] >> 7) == 1
        self.is_stereo = int(buf[2] >> 7) == 1
        self.signal_adc_level = int(buf[3] >> 4)


    def update(self):
        if self.band_limits == 'JP':
            self.frequency = min(max(self.frequency, Radio.FREQ_RANGE_JP[0]), Radio.FREQ_RANGE_JP[1])
        else:
            self.band_limits = 'US'
            self.frequency = min(max(self.frequency, Radio.FREQ_RANGE_US[0]), Radio.FREQ_RANGE_US[1])
        freqB = 4 * (self.frequency * 1000000 + 225000) / 32768
        buf = bytearray(5)
        buf[0] = int(freqB) >> 8 | self.mute_mode << 7 | self.search_mode << 6
        buf[1] = int(freqB) & 0xff
        buf[2] = self.search_direction << 7 | 1 << 4 | self.stereo_mode << 3
        try:
            buf[2] += Radio.ADC_BIT[Radio.ADC.index(self.search_adc_level)] << 5
        except:
            pass
        buf[3] = self.standby_mode << 6 | (self.band_limits == 'JP') << 5 | 1 << 4
        buf[3] += self.soft_mute_mode << 3 | self.high_cut_mode << 2 | self.stereo_noise_cancelling_mode << 1
        buf[4] = 0
        for i in range(5):
            print(hex(buf[i]))
        self._i2c.writeto(self._address, bytes(buf)) # writing whole buffer
        time.sleep(0.001)
        self.read()


if __name__ == '__main__':

    radio = Radio(freq=101.0)
    print('Frequency: FM {}\nReady: {}\nStereo: {}\nADC level: {}'.format(
        radio.frequency, radio.is_ready,  radio.is_stereo, radio.signal_adc_level
        ))
