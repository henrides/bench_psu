import machine
import asyncio
import time
import ujson as json

class ChannelModel():
    def __init__(self, channels):
        self._channels = {}
        for chan in channels:
            self._channels[chan.name()] = chan
        self._presets = []

        self._load_config()

    def use_preset(self, index):
        try:
            preset = self._presets[index]
            for ch_name, ch_conf in preset.items():
                chan = self._channels[ch_name]
                chan.v_set(ch_conf['v'])
                chan.i_set(ch_conf['i'])
            self._save_config()
        except:
            print('Preset {} not found'.format(index))
            for chan in self._channels.values():
                chan.v_set(5.0)
                chan.i_set(0.1)

    def save_preset(self, index):
        if index > (len(self._presets) - 1):
            for idx in range(index - (len(self._presets) - 1)):
                self._presets.append(None)
        preset = {}
        for ch_name, chan in self._channels.items():
            preset[ch_name] = {
                'v': chan.v_set(),
                'i': chan.i_set()
            }
        self._presets[index] = preset
        self._save_config()

    def _load_config(self):
        try:
            with open('conf.json', 'r') as conf:
                data = json.load(conf)
                for ch_name, ch_conf in data['lastValues'].items():
                    chan = self._channels[ch_name]
                    chan.v_set(ch_conf['v'])
                    chan.i_set(ch_conf['i'])
                self._presets = data['presets']
        except:
            print('No config found')
            for chan in self._channels.values():
                chan.v_set(5.0)
                chan.i_set(0.1)

    def _save_config(self):
        with open('conf.json', 'w') as conf:
            data = {
                'lastValues': {},
                'presets': self._presets
            }
            for ch_name, chan in self._channels.items():
                data['lastValues'][ch_name] = {
                    'v': chan.v_set(),
                    'i': chan.i_set()
                }
            json.dump(data, conf)

    def get_channel(self, channel_name):
        return self._channels[channel_name]

    def get_channels(self):
        return self._channels

    def v_set(self, channel_name, v=None):
        chan = self._channels[channel_name]
        chan.v_set(v)
        if v != None:
            self._save_config()

    def v_sense(self, channel_nanme):
        return self._channels[channel_name].v_sense()

    def i_set(self, channel_name, i=None):
        chan = self._channels[channel_name]
        chan.i_set(i)
        if i != None:
            self._save_config()

    def i_sense(self, channel_nanme):
        return self._channels[channel_name].i_sense()

class Channel():
    def __init__(self,
                 channel_name,
                 v_sense_adc: machine.ADC,
                 i_sense_adc: machine.ADC,
                 v_set_dac,
                 i_set_dac,
                 output_enable_button,
                 output_enable_state: machine.Pin):
        self._channel_name = channel_name
        self._v_sense_adc = v_sense_adc
        self._i_sense_adc = i_sense_adc
        self._v_set_dac = v_set_dac
        self._i_set_dac = i_set_dac
        self._output_enable_button = output_enable_button
        self._output_enable_state = output_enable_state

        self._v_sense = 0
        self._i_sense = 0

        self._output_enable_state.init(machine.Pin.OUT)
        self._output_enable_state.low() # Disable output on startup

        self._v_sense_div_ratio = 0.18018018 # Hardware is configured for 2 // 9.1 ~= 0.2 V/V
        self._i_sense_div_ratio = 1 # Hardware is configured for 1 V/A
        self.task = asyncio.create_task(self._go())

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
        self._output_enable_state.toggle()

    def output_enable(self, v=None):
        if v != None:
            self._output_enable_state.value(v)
        return self._output_enable_state()

    def get_output_enable_button(self):
        return self._output_enable_button
