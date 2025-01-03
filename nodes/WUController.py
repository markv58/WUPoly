"""Weather Underground Node Server Controller."""
import polyinterface
from nodes.WUNode import WUNode

LOGGER = polyinterface.LOGGER

class WUController(polyinterface.Controller):
    """Weather Underground NodeServer Controller Class"""
    
    id = 'controller'
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]

    def __init__(self, polyglot):
        """Initialize the controller."""
        super().__init__(polyglot)
        self.name = 'Weather Controller'
        self.address = 'controller'
        self.primary = self.address
        self.api_key = None
        self.location = None
        self.configured = False
        self.commands = {
            'QUERY': self.query,
            'DISCOVER': self.discover,
            'UPDATE_PROFILE': self.update_profile,
            'REMOVE_NOTICES_ALL': self.remove_notices_all
        }

    def start(self):
        """Start the controller."""
        try:
            LOGGER.info('Starting Weather Underground Controller')
            self.check_config()
            if not self.configured:
                LOGGER.error('Configuration not complete, skipping node creation')
                self.addNotice({'key': 'config', 'value': 'Missing configuration'})
                return
            self.removeNoticesAll()
            self.discover()
            self.setDriver('ST', 1)
        except Exception as err:
            LOGGER.error(f'Error starting controller: {err}')
            self.setDriver('ST', 0)

    def shortPoll(self):
        """Poll for quick-changing data."""
        try:
            for node in self.nodes.values():
                if hasattr(node, 'shortPoll'):
                    node.shortPoll()
        except Exception as err:
            LOGGER.error(f'Error in shortPoll: {err}')

    def longPoll(self):
        """Poll for slow-changing data."""
        try:
            for node in self.nodes.values():
                if hasattr(node, 'longPoll'):
                    node.longPoll()
        except Exception as err:
            LOGGER.error(f'Error in longPoll: {err}')

    def query(self, command=None):
        """Query all nodes."""
        try:
            self.reportDrivers()
            for node in self.nodes.values():
                node.reportDrivers()
        except Exception as err:
            LOGGER.error(f'Error querying nodes: {err}')

    def discover(self, *args, **kwargs):
        """Discover nodes - required by ISY."""
        try:
            if 'weather' not in self.nodes and self.configured:
                self.addNode(WUNode(
                    self,
                    'weather',
                    'weather',
                    'Weather Station',
                    api_key=self.api_key,
                    location=self.location
                ))
        except Exception as err:
            LOGGER.error(f'Error discovering nodes: {err}')

    def delete(self):
        """Delete the node server from Polyglot."""
        try:
            LOGGER.info('Deleting Weather Underground Node Server')
            self.stop()
        except Exception as err:
            LOGGER.error(f'Error deleting node server: {err}')

    def stop(self):
        """Stop the node server."""
        try:
            self.setDriver('ST', 0)
            for node in self.nodes.values():
                if hasattr(node, 'stop'):
                    node.stop()
            self.poly.stop()
        except Exception as err:
            LOGGER.error(f'Error stopping node server: {err}')

    def check_config(self):
        """Verify required configuration items are set."""
        try:
            self.removeNoticesAll()
            default_params = {
                'api_key': 'Enter your Weather API key',
                'location': 'Enter location (ZIP, city,state, or lat,lon)'
            }
            
            self.configured = True
            for param, default in default_params.items():
                if param not in self.polyConfig:
                    self.addCustomParam({param: default})
                    LOGGER.error(f'Missing {param} parameter')
                    self.configured = False
                elif not self.polyConfig[param]:
                    LOGGER.error(f'{param} parameter is empty')
                    self.configured = False

            self.api_key = self.polyConfig.get('api_key')
            self.location = self.polyConfig.get('location')
            
            if not self.api_key or not self.location:
                self.addNotice({
                    'key': 'config',
                    'value': 'Please set API key and location in custom configuration.'
                })
        except Exception as err:
            LOGGER.error(f'Error checking configuration: {err}')
            self.configured = False

    def remove_notices_all(self, command=None):
        """Remove all notices."""
        try:
            self.removeNoticesAll()
        except Exception as err:
            LOGGER.error(f'Error removing notices: {err}')

    def update_profile(self, command=None):
        """Update the profile files on ISY."""
        try:
            self.poly.updateProfile()
        except Exception as err:
            LOGGER.error(f'Error updating profile: {err}') 