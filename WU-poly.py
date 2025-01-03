#!/usr/bin/env python3

"""
Polyglot v3 node server for Weather Underground
Copyright (C) 2024 Robert Paauwe

MIT License
"""

import sys
import time
import polyinterface
from nodes import WUController

LOGGER = polyinterface.LOGGER

if __name__ == "__main__":
    try:
        LOGGER.info('Starting Weather Underground Node Server')
        polyglot = polyinterface.Interface('WeatherUnderground')
        polyglot.start()
        
        control = WUController(polyglot)
        control.runForever()
        
    except (KeyboardInterrupt, SystemExit):
        LOGGER.warning("Received interrupt or exit signal, shutting down...")
        sys.exit(0)
    
    except Exception as err:
        LOGGER.error('Caught exception: {0}\n'.format(err), exc_info=True)
        sys.exit(1) 