#!/bin/sh

mpremote mip install github:peterhinch/micropython-async/v3/primitives

mpremote fs mkdir mip_modules
mpremote fs cp mip_modules/mcp23Sxx.py :mip_modules/mcp23Sxx.py
mpremote fs cp mip_modules/x_pin.py :mip_modules/x_pin.py

mpremote fs mkdir mip_modules/display_drivers
mpremote fs cp mip_modules/display_drivers/__init__.py :mip_modules/display_drivers/__init__.py
mpremote fs cp mip_modules/display_drivers/display_driver.py :mip_modules/display_drivers/display_driver.py
mpremote fs mkdir mip_modules/display_drivers/ks0108
mpremote fs cp mip_modules/display_drivers/ks0108/__init__.py :mip_modules/display_drivers/ks0108/__init__.py
mpremote fs cp mip_modules/display_drivers/ks0108/pio_ks0108.py :mip_modules/display_drivers/ks0108/pio_ks0108.py
mpremote fs mkdir mip_modules/display_drivers/bmp
mpremote fs cp mip_modules/display_drivers/bmp/__init__.py :mip_modules/display_drivers/bmp/__init__.py
mpremote fs cp mip_modules/display_drivers/bmp/bmp_display_driver.py :mip_modules/display_drivers/bmp/bmp_display_driver.py

mpremote fs mkdir mip_modules/spi_adc
mpremote fs cp mip_modules/spi_adc/__init__.py :mip_modules/spi_adc/__init__.py
mpremote fs cp mip_modules/spi_adc/spi_adc.py :mip_modules/spi_adc/spi_adc.py
mpremote fs cp mip_modules/spi_adc/mcp3xxx.py :mip_modules/spi_adc/mcp3xxx.py

mpremote fs mkdir mip_modules/spi_dac
mpremote fs cp mip_modules/spi_dac/__init__.py :mip_modules/spi_dac/__init__.py
mpremote fs cp mip_modules/spi_dac/mcp48x2.py :mip_modules/spi_dac/mcp48x2.py

mpremote fs cp channel_ctrl.py :channel_ctrl.py
mpremote fs cp channel_view.py :channel_view.py
mpremote fs cp channel_model.py :channel_model.py
mpremote fs cp main.py :main.py

mpremote soft-reset
