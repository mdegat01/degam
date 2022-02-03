"""Adds config flow for Netgear."""
import asyncio
from concurrent.futures import ProcessPoolExecutor

from pynetgear_enhanced import NetgearEnhanced as Netgear
import voluptuous as vol

from homeassistant import config_entries
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from . import get_connection


config = {
    vol.Optional(CONF_SSL, default=False): cv.boolean,
    vol.Optional(CONF_HOST, default=""): cv.string,
    vol.Optional(CONF_PORT): cv.port,
    vol.Optional(CONF_USERNAME, default=""): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
}

class NetgearFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Netgear."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            loop = asyncio.get_event_loop()
            try:
                netgear, success = get_connection(loop, user_input, True)
                if success == True:
                    router_info = netgear.get_lan_config_sec_info()
                    await self.async_set_unique_id(
                        router_info[ROUTER_MAC_FIELD], raise_on_progress=False
                    )
                    return self.async_create_entry(
                        title=user_input[CONF_NAME], data=user_input
                    )
                else:
                    errors["base"] = ERROR_CANNOT_CONNECT
            except asyncio.exceptions.TimeoutError:
                errors["base"] = ERROR_TIMEOUT

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(config),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Options callback for Netgear."""
        return NetgearOptionsFlowHandler(config_entry)


class NetgearOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for Netgear."""

    def __init__(self, config_entry):
        """Initialize Netgear options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_USERNAME, default=""): cv.string,
                    vol.Required(CONF_PASSWORD): cv.string,
                }
            ),
        )
