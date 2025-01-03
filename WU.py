#!/usr/bin/env python3
"""
Weather Underground Node Server for Universal Devices ISY994i.
For more information about the ISY994i and Polyglot, visit:
https://www.universal-devices.com
"""
import sys
import time
import polyinterface
from nodes import WUController

LOGGER = polyinterface.LOGGER

if __name__ == "__main__":
    try:
        LOGGER.info('Starting Weather Underground Node Server')
        
        # Create Polyglot interface
        polyglot = polyinterface.Interface('WeatherUnderground')
        
        # Initialize version and git info
        polyglot.setCustomParamsDoc()
        
        # Start polyglot
        polyglot.start()
        
        # Create and run the controller
        control = WUController(polyglot)
        control.runForever()
        
    except (KeyboardInterrupt, SystemExit):
        LOGGER.warning("Received interrupt or exit signal, shutting down...")
        polyglot.stop()
        sys.exit(0)
    
    except Exception as err:
        LOGGER.error('Caught exception: {0}\n'.format(err), exc_info=True)
        sys.exit(1) 