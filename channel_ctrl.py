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
        return self._output_enable

class ChannelCtrl():
    def __init__(self, channel_model):
        self._channel_model = channel_model

    def get_channel_names(self):
        return list(sorted(self._channel_model.get_channels().keys()))

    def get_channel_output_enable_button(self, channel_name):
        return self._channel_model.get_channel(channel_name).get_output_enable_button()

    async def get_channel_status(self, channel_name):
        channel = self._get_channel(channel_name)
        name = channel.name()
        v_sense = channel.v_sense()
        i_sense = channel.i_sense()
        v_set = channel.v_set()
        i_set = channel.i_set()
        output_enable = channel.output_enable()
        return ChannelStatus(name, v_sense, i_sense, v_set, i_set, output_enable)

    def set_channel_v(self, channel_name, val):
        self._channel_model.v_set(channel_name, val)

    def set_channel_i(self, channel_name, val):
        self._channel_model.i_set(channel_name, val)

    def use_preset(self, preset_index):
        self._channel_model.use_preset(preset_index)

    def save_preset(self, preset_index):
        self._channel_model.save_preset(preset_index)

    def toggle_channel_output(self, channel_name):
        channel = self._get_channel(channel_name)
        channel.toggle_output()

    def _get_channel(self, channel_name):
        return self._channel_model.get_channel(channel_name)
