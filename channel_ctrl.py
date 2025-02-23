import random

class ChannelStatus():
    def __init__(self, name, v_sense, i_sense, v_set, i_set, output_enable):
        self._name = name
        self._v_sense = v_sense
        self._i_sense = i_sense
        self._v_set = v_set
        self._i_set = i_set
        self._output_enable = output_enable

    def name(self):
        return self._name

    def v_sense(self):
        return self._v_sense

    def i_sense(self):
        return self._i_sense

    def v_set(self):
        return self._v_set

    def i_set(self):
        return self._i_set

    def output_enable(self):
        return this._output_enable

class ChannelCtrl():
    def __init__(self, channel1, channel2):
        self._channel1 = channel1
        self._channel2 = channel2

    async def get_channel_status(self, channel: int):
        channel = self._get_channel(channel)
        name = channel.name()
        v_sense = channel.v_sense()
        i_sense = channel.i_sense()
        v_set = channel.v_set()
        i_set = channel.i_set()
        output_enable = channel.output_enable()
        return ChannelStatus(name, v_sense, i_sense, v_set, i_set, output_enable)

    def set_channel_v(self, channel: int, val):
        channel = self._get_channel(channel)
        channel.v_set(val)

    def set_channel_i(self, channel: int, val):
        channel = self._get_channel(channel)
        channel.i_set(val)

    def toggle_channel_output(self, channel: int):
        channel = self._get_channel(channel)
        channel.toggle_output()

    def _get_channel(self, channel: int):
        return self._channel1 if channel == 1 else self._channel2
