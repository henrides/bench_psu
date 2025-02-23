import machine
import asyncio
import time

class Channel():
    def __init__(self,
                 channel_name,
                 v_sense_adc: machine.ADC,
                 i_sense_adc: machine.ADC,
                 v_set_dac,
                 i_set_dac,
                 output_enable: machine.Pin):
        self._channel_name = channel_name
        self._v_sense_adc = v_sense_adc
        self._i_sense_adc = i_sense_adc
        self._v_set_dac = v_set_dac
        self._i_set_dac = i_set_dac
        self._output_enable = output_enable

        self._v_sense = 0
        self._i_sense = 0

        self._output_enable.init(machine.Pin.OUT)
        self._output_enable.low() # Disable output on startup

        self._v_sense_div_ratio = 0.18018018 # Hardware is configured for 2 // 9.1 ~= 0.2 V/V
        self._i_sense_div_ratio = 1 # Hardware is configured for 1 V/A
        self.task = asyncio.create_task(self._go())

        self.v_set(5)
        self.i_set(0.1)

    async def _go(self):
        while True:
            self._v_sense = (self._v_sense_adc.read_uv() / 1_000_000) / self._v_sense_div_ratio
            self._i_sense = (self._i_sense_adc.read_uv() / 1_000_000) / self._i_sense_div_ratio
            await asyncio.sleep_ms(1000)

    def name(self):
        return self._channel_name

    # Get/Set voltage config (in Volt)
    def v_set(self, v=None):
        if v != None:
            self._v_set = v
            self._v_set_dac.write_uv((self._v_set * (self._v_sense_div_ratio / 2)) * 1_000_000)
        else:
            return self._v_set

    # Get the sensed voltage (in Volt)
    def v_sense(self):
        return self._v_sense

    # Get/Set maximum current config (in Amp)
    def i_set(self, i=None):
        if i != None:
            self._i_set = i
            self._i_set_dac.write_uv((self._i_set * self._i_sense_div_ratio) * 1_000_000)
        else:
            return self._i_set

    # Get the sensed current (in Amp)
    def i_sense(self):
        return self._i_sense

    def toggle_output(self):
        self._output_enable.toggle()

    def output_enable(self, v=None):
        if v != None:
            self._output_enable.value(v)
        return self._output_enable()

