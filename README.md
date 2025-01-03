# Weather Underground Node Server

This node server integrates Weather Underground data into the ISY994i using Polyglot v3.

## Installation

1. Install from the Polyglot Store
2. Add the node server to Polyglot
3. Configure your Weather API key and location

## Configuration

The following custom parameters need to be configured:
* `api_key` - Your Weather API key from weatherapi.com
* `location` - Location in one of these formats:
  * ZIP code (e.g., "90210")
  * City,State (e.g., "Seattle,WA")
  * Latitude,Longitude (e.g., "47.6062,-122.3321")

## Node Types

### Weather Controller Node
* Status: Online/Offline

### Weather Node
* Temperature (°F)
* Humidity (%)
* Barometric Pressure (inHg)
* Wind Direction (degrees)
* Wind Speed (mph)
* Rain Rate (in/hr)
* Chance of Rain (%)
* Current Conditions (text)

## Requirements
* Polyglot V3
* ISY994i firmware 5.3.x or later
* Weather API key from weatherapi.com

## Release Notes

* 1.0.0: Initial release
