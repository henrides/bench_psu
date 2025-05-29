import framebuf
import display_drivers
import asyncio
import random
import time

V_SET_MAXIMUM=20
V_SET_COARSE_INCREMENT=1
V_SET_FINE_INCREMENT=0.1
I_SET_MAXIMUM=1
I_SET_COARSE_INCREMENT=0.1
I_SET_FINE_INCREMENT=0.01

class ChannelView():
    def __init__(self,
                 ctrl,
                 display_driver: display_drivers.DisplayDriver,
                 coarse_encoder,
                 coarse_encoder_button,
                 fine_encoder,
                 fine_encoder_button,
                 preset_buttons) -> None:
        self._ctrl = ctrl
        self._width = 128
        self._height = 64
        self._buffer = bytearray(self._width * (self._height // 8))
        self._framebuf = framebuf.FrameBuffer(self._buffer,
                                              self._width,
                                              self._height,
                                              framebuf.MONO_VLSB)
        self._driver = display_driver

        self._coarse_encoder = coarse_encoder
        self._coarse_enc_button_task = asyncio.create_task(
                self._encoder_press(coarse_encoder_button))
        self._coarse_enc_task = asyncio.create_task(
                self._encoder_turn(coarse_encoder,
                                   V_SET_COARSE_INCREMENT,
                                   I_SET_COARSE_INCREMENT))

        self._fine_encoder = fine_encoder
        self._fine_enc_button_task = asyncio.create_task(
                self._encoder_press(fine_encoder_button))
        self._fine_enc_task = asyncio.create_task(
                self._encoder_turn(fine_encoder,
                                   V_SET_FINE_INCREMENT,
                                   I_SET_FINE_INCREMENT))

        self._channels = self._ctrl.get_channel_names()

        self._i_set = {}
        self._v_set = {}
        self._ch_out_en_button_task = {}

        for chan in self._channels:
            self._i_set[chan] = 0
            self._v_set[chan] = 0
            out_en_button = self._ctrl.get_channel_output_enable_button(chan)
            self._ch_out_en_button_task[chan] = asyncio.create_task(
                    self._out_enable_press(out_en_button, chan))

        self._preset_buttons_press_tasks = {}
        self._preset_buttons_long_press_tasks = {}
        self._preset_buttons_long_press_release = []
        for index, preset_button in enumerate(preset_buttons):
            self._preset_buttons_press_tasks[index] = asyncio.create_task(
                    self._preset_button_press(preset_button, index))
            self._preset_buttons_long_press_tasks[index] = asyncio.create_task(
                    self._preset_button_long_press(preset_button, index))
            self._preset_buttons_long_press_release.append(False)

        self._init_framebuffer()
        self._i_selected_channel = None
        self._v_selected_channel = None

        self._edit_mode = False
        self._last_change_ticks = 0

        self._saving_preset = None

        self.task = asyncio.create_task(self._go())

    def _init_framebuffer(self):
        self._framebuf.fill(0)
        for chan in self._channels:
            x_offset = 64 * self._channels.index(chan)
            self._framebuf.rect(1+x_offset, 1, 62, 62, 1)
            self._framebuf.rect(1+x_offset, 1, 62,  11, 1, 0)

    async def _refresh(self) -> None:
        #start = time.ticks_us()
        for chan in self._channels:
            await self._refresh_channel(chan, 64 * self._channels.index(chan))
        self._driver.print_buffer(self._buffer)
        #print('_refresh total {}'.format(time.ticks_us() - start))

    def _refresh_header(self, channel_status, x_offset):
        self._framebuf.rect(1+x_offset, 1, 62,  11, 1, channel_status.output_enable())
        self._framebuf.text(channel_status.name(), 18+x_offset, 3, not channel_status.output_enable())
        pass

    async def _refresh_channel(self, channel, x_offset):
        channel_status = await self._ctrl.get_channel_status(channel)
        self._framebuf.rect(0+x_offset, 0, 64, 64, 0, 1)
        self._framebuf.rect(1+x_offset, 1, 62, 62, 1, 0)

        self._refresh_header(channel_status, x_offset)
        v_sense = channel_status.v_sense()
        i_sense = channel_status.i_sense()
        if not self._edit_mode:
            self._v_set[channel] = channel_status.v_set()
            self._i_set[channel] = channel_status.i_set()
        self._framebuf.rect(2+x_offset, 12, 60, 50, 0, 1)

        v_edit = False
        if self._v_selected_channel == channel and self._edit_mode:
            self._framebuf.rect(12+x_offset, 13, 32, 9, 1, 1)
            v_edit = True
        self._framebuf.text(self._truncate_four_digits(self._v_set[channel]),
                            12+x_offset, 16, 0 if v_edit else 1)
        self._framebuf.text('mV' if self._v_set[channel] < 1 else ' V',
                            44+x_offset, 16)
        if self._v_selected_channel == channel:
            self._framebuf.hline(4+x_offset, 24, 56, 1)

        i_edit = False
        if self._i_selected_channel == channel and self._edit_mode:
            self._framebuf.rect(12+x_offset, 25, 32, 9, 1, 1)
            i_edit = True
        self._framebuf.text(self._truncate_four_digits(self._i_set[channel]),
                            12+x_offset, 26, 0 if i_edit else 1)
        self._framebuf.text('mA' if self._i_set[channel] < 1 else ' A',
                            44+x_offset, 26)
        if self._i_selected_channel == channel:
            self._framebuf.hline(4+x_offset, 34, 56, 1)

        self._framebuf.text(self._truncate_four_digits(v_sense),
                            12+x_offset, 40)
        self._framebuf.text('mV' if self._v_set[channel] < 1 else ' V',
                            44+x_offset, 40)
        self._framebuf.text(self._truncate_four_digits(i_sense),
                            12+x_offset, 50)
        self._framebuf.text('mA' if self._i_set[channel] < 1 else ' A',
                            44+x_offset, 50)

        if self._saving_preset is not None:
            message_x_offset = ((self._width - 64) // 2) - 8
            message_y_offset = ((self._height - 16) // 2) - 4
            self._framebuf.rect(message_x_offset, message_y_offset, 80, 24, 0, 1)
            self._framebuf.rect(message_x_offset+2, message_y_offset+2, 76, 20, 1, 0)
            self._framebuf.text('Preset {}'.format(self._saving_preset + 1),
                                message_x_offset+8, message_y_offset+4, 1)
            self._framebuf.text(' Saved. ', message_x_offset+8, message_y_offset+12, 1)

    def _truncate_four_digits(self, value):
        if value >= 100:
            return f'{value:.0f}'
        elif value >= 10:
            return f'{value:.1f}'
        elif value >= 1:
            return f'{value:.2f}'
        elif value < 0.00001:
            return '0'
        else:
            new_value = value * 1000
            return self._truncate_four_digits(new_value)

    async def _encoder_turn(self, encoder, v_increment, i_increment):
        prev_value = 0
        async for event in encoder:
            if self._edit_mode:
                if event > prev_value:
                    self._adjust_value(True, v_increment, i_increment)
                elif event < prev_value:
                    self._adjust_value(False, v_increment, i_increment)
            else:
                self._next_selection(event > prev_value)
            prev_value = event
            self._last_change_ticks = time.ticks_us()
            await self._refresh()

    def _adjust_value(self, add, v_increment, i_increment):
        if add:
            if self._v_selected_channel != None:
                self._v_set[self._v_selected_channel] += v_increment
                if self._v_set[self._v_selected_channel] > V_SET_MAXIMUM:
                    self._v_set[self._v_selected_channel] = V_SET_MAXIMUM
            elif self._i_selected_channel != None:
                self._i_set[self._i_selected_channel] += i_increment
                if self._i_set[self._i_selected_channel] > I_SET_MAXIMUM:
                    self._i_set[self._i_selected_channel] = I_SET_MAXIMUM
        else:
            if self._v_selected_channel != None:
                self._v_set[self._v_selected_channel] -= v_increment
                if self._v_set[self._v_selected_channel] < V_SET_FINE_INCREMENT:
                    self._v_set[self._v_selected_channel] = V_SET_FINE_INCREMENT
            elif self._i_selected_channel != None:
                self._i_set[self._i_selected_channel] -= i_increment
                if self._i_set[self._i_selected_channel] < I_SET_FINE_INCREMENT:
                    self._i_set[self._i_selected_channel] = I_SET_FINE_INCREMENT

    def _set_selection(self, v_sel, i_sel):
        if v_sel != None:
            self._v_selected_channel = v_sel
            self._i_selected_channel = None
            self._edit_mode = False
        elif i_sel != None:
            self._i_selected_channel = i_sel
            self._v_selected_channel = None
            self._edit_mode = False

    def _next_channel(self, channel, cw=None):
        index = self._channels.index(channel)
        if cw:
            index += 1
            if index >= len(self._channels):
                return self._channels[0]
        else:
            index -= 1
        return self._channels[index]

    def _next_selection(self, cw=None):
        if self._v_selected_channel != None:
            if cw:
                self._set_selection(None, self._v_selected_channel)
            else:
                self._set_selection(None, self._next_channel(self._v_selected_channel, cw))
        elif self._i_selected_channel != None:
            if cw:
                self._set_selection(self._next_channel(self._i_selected_channel, cw), None)
            else:
                self._set_selection(self._i_selected_channel, None)
        else:
            self._set_selection(self._channels[0], None)

    async def _encoder_press(self, button) -> None:
        while True:
            button.press.clear()
            await button.press.wait()
            print("encoder pressed")
            if self._edit_mode:
                if self._v_selected_channel != None:
                    self._ctrl.set_channel_v(self._v_selected_channel,
                                             self._v_set[self._v_selected_channel])
                    self._edit_mode = False
                    self._v_selected_channel = None
                elif self._i_selected_channel != None:
                    self._ctrl.set_channel_i(self._i_selected_channel,
                                             self._i_set[self._i_selected_channel])
                    self._edit_mode = False
                    self._i_selected_channel = None
            elif self._v_selected_channel != None or self._i_selected_channel != None:
                self._edit_mode = True
            else:
                self._next_selection()
            self._last_change_ticks = time.ticks_us()
            await self._refresh()

    async def _out_enable_press(self, button, channel) -> None:
        while True:
            button.press.clear()
            await button.press.wait()
            #self._ctrl.toggle_channel_output(channel)
            self._ctrl.set_channel_v(channel, random.randint(3,12))
            await self._refresh()

    async def _preset_button_press(self, button, index) -> None:
        while True:
            button.release.clear()
            await button.release.wait()
            if not self._preset_buttons_long_press_release[index]:
                self._ctrl.use_preset(index)
            else:
                self._preset_buttons_long_press_release[index] = False
            await self._refresh()

    async def _preset_button_long_press(self, button, index) -> None:
        while True:
            button.long.clear()
            await button.long.wait()
            if self._saving_preset is None:
                self._preset_buttons_long_press_release[index] = True
                self._ctrl.save_preset(index)
                self._saving_preset = index
                await self._refresh()
                await asyncio.sleep_ms(2000)
                self._saving_preset = None

    async def _go(self) -> None:
        while True:
            if self._v_selected_channel != None or self._i_selected_channel != None:
                if time.ticks_diff(time.ticks_us(), self._last_change_ticks) > 5_000_000:
                    self._edit_mode = False
                    self._v_selected_channel = None
                    self._i_selected_channel = None

            await self._refresh()
            await asyncio.sleep_ms(1000)
            
