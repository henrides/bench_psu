import platform

import sys
if 'Linux' in platform.platform():
    sys.path.append('./mock')
sys.path.append('./mip_modules')

from machine import Pin, SPI
import time
import asyncio
from display_drivers import ks0108
from spi_adc import mcp3xxx
from spi_dac import mcp48x2
import mcp23Sxx
from x_pin import XPin
from primitives import EButton, Encoder

import channel_view
import channel_ctrl
import channel_model

if 'Linux' in platform.platform():
    Pin.path = 'sim'

width = 128
height = 64
display_driver = ks0108.PioKs0108(width, height, Pin(8, Pin.OUT), Pin(12, Pin.OUT), Pin(0, Pin.OUT), Pin(13, Pin.OUT))


spi = SPI(0, baudrate=8000000, polarity=1, phase=1, bits=8, firstbit=SPI.MSB, sck=Pin(18), miso=Pin(16), mosi=Pin(19))

adc_ch1_cs = Pin(26, Pin.OUT)
adc_ch1_vsense = mcp3xxx.Mcp3xxx(spi, adc_ch1_cs, mcp3xxx.CHANNEL_0, 10, 4.096)
adc_ch1_isense = mcp3xxx.Mcp3xxx(spi, adc_ch1_cs, mcp3xxx.CHANNEL_1, 10, 4.096)

dac_ch1_cs = Pin(27, Pin.OUT)
dac_ch1_vset = mcp48x2.Mcp48x2(spi, dac_ch1_cs, mcp48x2.CHANNEL_0, gain=mcp48x2.GAIN_2)
dac_ch1_iset = mcp48x2.Mcp48x2(spi, dac_ch1_cs, mcp48x2.CHANNEL_1, gain=mcp48x2.GAIN_2)

out_en_ch1 = Pin(28, Pin.OUT)

adc_ch2_cs = Pin(20, Pin.OUT)
adc_ch2_vsense = mcp3xxx.Mcp3xxx(spi, adc_ch2_cs, mcp3xxx.CHANNEL_0, 10, 4.096)
adc_ch2_isense = mcp3xxx.Mcp3xxx(spi, adc_ch2_cs, mcp3xxx.CHANNEL_1, 10, 4.096)

dac_ch2_cs = Pin(21, Pin.OUT)
dac_ch2_vset = mcp48x2.Mcp48x2(spi, dac_ch2_cs, mcp48x2.CHANNEL_0, gain=mcp48x2.GAIN_2)
dac_ch2_iset = mcp48x2.Mcp48x2(spi, dac_ch2_cs, mcp48x2.CHANNEL_1, gain=mcp48x2.GAIN_2)

out_en_ch2 = Pin(22, Pin.OUT)

ioext_cs = Pin(17, Pin.OUT)
ioext_cs.high()
ioext = mcp23Sxx.MCP23S17(spi, ioext_cs, mcp23Sxx.IOCON_HAEN|mcp23Sxx.IOCON_MIRROR, Pin(14, Pin.IN, Pin.PULL_UP))
ioext.read_gpio() # initialize internal gpio state

coarse_encoder = Encoder(XPin(ioext, 0, Pin.IN, Pin.PULL_UP), XPin(ioext, 1, Pin.IN, Pin.PULL_UP))
coarse_encoder_button = EButton(XPin(ioext, 2, Pin.IN, Pin.PULL_UP))
fine_encoder = Encoder(XPin(ioext, 3, Pin.IN, Pin.PULL_UP), XPin(ioext, 4, Pin.IN, Pin.PULL_UP))
fine_encoder_button = EButton(XPin(ioext, 5, Pin.IN, Pin.PULL_UP))
ch1_out_en_button = EButton(XPin(ioext, 6, Pin.IN, Pin.OUT))
ch2_out_en_button = EButton(XPin(ioext, 7, Pin.IN, Pin.OUT))

# Override with simulated drivers in dev
if 'Linux' in platform.platform():
    from display_drivers import bmp
    print('Using bmp driver')

    display_driver = bmp.Bmp('sim/display.bmp', width, height)

    coarse_encoder_button = EButton(Pin(2, Pin.IN, Pin.PULL_UP))
    fine_encoder_button = EButton(Pin(5, Pin.IN, Pin.PULL_UP))
    ch1_out_en_button = EButton(Pin(6, Pin.IN, Pin.OUT))
    ch2_out_en_button = EButton(Pin(7, Pin.IN, Pin.OUT))

async def main():
    print('Starting...')
    display_driver.init()
    print('display driver initialized...')
    channel1 = channel_model.Channel('CH 1',
                                     adc_ch1_vsense,
                                     adc_ch1_isense,
                                     dac_ch1_vset,
                                     dac_ch1_iset,
                                     out_en_ch1)
    print('channel 1 initialized...')
    channel2 = channel_model.Channel('CH 2',
                                     adc_ch2_vsense,
                                     adc_ch2_isense,
                                     dac_ch2_vset,
                                     dac_ch2_iset,
                                     out_en_ch2)
    print('channel 2 initialized...')
    ch_ctrl = channel_ctrl.ChannelCtrl(channel1, ch1_out_en_button, channel2, ch2_out_en_button)
    print('channel controller initialized...')
    ch_view = channel_view.ChannelView(ch_ctrl,
                                       display_driver,
                                       coarse_encoder,
                                       coarse_encoder_button,
                                       fine_encoder,
                                       fine_encoder_button)
    print('view init done')
    await asyncio.gather(ch_view.task, channel1.task, channel2.task)
    print('Done')

asyncio.run(main())
