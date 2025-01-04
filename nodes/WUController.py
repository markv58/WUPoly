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
        
        # Define custom parameters
        self.params = {
            'api_key': {
                'name': 'Weather API Key',
                'description': 'Your API key from weatherapi.com',
                'isRequired': True,
                'isConfig': True,
                'default': 'Enter your Weather API key'
            },
            'location': {
                'name': 'Location',
                'description': 'Location as ZIP code, City,State, or Lat,Lon',
                'isRequired': True,
                'isConfig': True,
                'default': 'Enter location (ZIP, city,state, or lat,lon)'
            }
        }
        
        # Add custom parameters if they don't exist
        for param, data in self.params.items():
            if param not in self.polyConfig:
                self.addCustomParam({param: data['default']})
        
        # Set custom parameters doc
        self.poly.setCustomParamsDoc(self.params)
        
        # Define commands
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
                LOGGER.error('Configuration not complete')
                self.setDriver('ST', 0)
                return
            self.discover()
            self.setDriver('ST', 1)
        except Exception as err:
            LOGGER.error(f'Error starting controller: {err}')
            self.setDriver('ST', 0)

    def shortPoll(self):
        """Poll for quick-changing data."""
        try:
            for node in self.nodes.values():
                if hasattr(node, 'shortPoll') and node.address != self.address:
                    node.shortPoll()
        except Exception as err:
            LOGGER.error(f'Error in shortPoll: {err}')

    def longPoll(self):
        """Poll for slow-changing data."""
        try:
            for node in self.nodes.values():
                if hasattr(node, 'longPoll') and node.address != self.address:
                    node.longPoll()
        except Exception as err:
            LOGGER.error(f'Error in longPoll: {err}')

    def query(self, command=None):
        """Query all nodes."""
        try:
            self.reportDrivers()
            for node in self.nodes.values():
                if node.address != self.address:
                    node.reportDrivers()
        except Exception as err:
            LOGGER.error(f'Error querying nodes: {err}')

    def discover(self, *args, **kwargs):
        """Discover nodes - required by ISY."""
        try:
            if not self.configured:
                LOGGER.error('Cannot discover, not configured')
                self.setDriver('ST', 0)
                return
            if 'weather' not in self.nodes:
                LOGGER.info('Creating Weather Node')
                self.addNode(WUNode(
                    self,
                    'weather',
                    'weather',
                    'Weather Station',
                    api_key=self.api_key,
                    location=self.location
                ))
                self.setDriver('ST', 1)
        except Exception as err:
            LOGGER.error(f'Error discovering nodes: {err}')
            self.setDriver('ST', 0)

    def delete(self):
        """Delete the node server from Polyglot."""
        try:
            self.stop()
        except Exception as err:
            LOGGER.error(f'Error deleting node server: {err}')

    def stop(self):
        """Stop the node server."""
        try:
            self.setDriver('ST', 0)
            for node in self.nodes.values():
                if hasattr(node, 'stop') and node.address != self.address:
                    node.stop()
            self.poly.stop()
        except Exception as err:
            LOGGER.error(f'Error stopping node server: {err}')

    def check_config(self):
        """Verify required configuration items are set."""
        try:
            self.removeNoticesAll()
            
            # Get the configuration parameters
            self.api_key = self.polyConfig.get('api_key')
            self.location = self.polyConfig.get('location')
            
            # Check if parameters are set and valid
            self.configured = True
            
            # Check API key
            if not self.api_key or self.api_key == self.params['api_key']['default']:
                self.configured = False
                LOGGER.error('Missing or invalid API key')
                self.addNotice({'key': 'api_key', 'value': 'Please enter your Weather API key'})
                
            # Check location
            if not self.location or self.location == self.params['location']['default']:
                self.configured = False
                LOGGER.error('Missing or invalid location')
                self.addNotice({'key': 'location', 'value': 'Please enter a valid location'})
                
            # Set status based on configuration
            self.setDriver('ST', 1 if self.configured else 0)
                
        except Exception as err:
            LOGGER.error(f'Error checking configuration: {err}')
            self.configured = False
            self.setDriver('ST', 0)

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