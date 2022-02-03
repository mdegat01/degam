import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from datetime import timedelta

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)

OPTIONS_CONFIG = {
    vol.Optional(CONF_USERNAME, default=""): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
}

NETGEAR_CONFIG = OPTIONS_CONFIG.extend({
    vol.Optional(CONF_SSL, default=False): cv.boolean,
    vol.Optional(CONF_HOST, default=""): cv.string,
    vol.Optional(CONF_PORT): cv.port,
})

TEST_TIMEOUT = 5

UPDATE_INTERVAL = timedelta(minutes=1)
DOMAIN = "Netgear"
ROUTER_MAC_FIELD = 'NewLANMACAddress'
ERROR_CANNOT_CONNECT = 'cannot_connect'
ERROR_TIMEOUT = 'timeout_error'
