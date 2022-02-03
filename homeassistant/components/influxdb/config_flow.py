"""Config flow for InfluxDB integration."""
import logging
import json
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from .const import (
    DOMAIN,
    CONF_API_VERSION,
    CONF_SSL,
    CONF_HOST,
    CONF_PORT,
    CONF_PATH,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_VERIFY_SSL,
    CONF_TOKEN,
    CONF_ORG,
    CONF_BUCKET,
    CONF_DB_NAME,
    DEFAULT_SSL_V1,
    DEFAULT_SSL_V2,
    DEFAULT_API_VERSION,
    API_VERSION_2,
    DEFAULT_HOST_V1,
    DEFAULT_HOST_V2,
    DEFAULT_PORT_V1,
    DEFAULT_BUCKET,
    DEFAULT_DATABASE,
    DEFAULT_VERIFY_SSL,
)
from . import (
    INFLUX_SCHEMA,
    get_influx_connection,
)

API_VERSION_SCHEMA = vol.Schema({
    vol.Optional(CONF_API_VERSION, default=DEFAULT_API_VERSION): vol.In({
        DEFAULT_API_VERSION: "InfluxDB V1.1 to V1.7",
        API_VERSION_2: "InfluxDB V1.8 or 2.x",
    }),
})
CONNECTION_SCHEMA_V1 = vol.Schema({
    vol.Optional(CONF_SSL, default=DEFAULT_SSL_V1): bool,
    vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    vol.Optional(CONF_HOST, default=DEFAULT_HOST_V1): str, 
    vol.Optional(CONF_PORT, default=DEFAULT_PORT_V1): vol.Coerce(int),
    vol.Optional(CONF_PATH): str,
    vol.Optional(CONF_USERNAME): str,
    vol.Optional(CONF_PASSWORD): str,
    vol.Required(CONF_DB_NAME, description={"suggested_value": DEFAULT_DATABASE}): str,
})
CONNECTION_SCHEMA_V2 = vol.Schema({
    vol.Optional(CONF_SSL, default=DEFAULT_SSL_V2): bool,
    vol.Optional(CONF_HOST, default=DEFAULT_HOST_V2): str, 
    vol.Optional(CONF_PORT): vol.Coerce(int),
    vol.Optional(CONF_PATH): str,
    vol.Required(CONF_TOKEN): str,
    vol.Required(CONF_ORG): str,
    vol.Required(CONF_BUCKET,description= {"suggested_value": DEFAULT_BUCKET}): str,
})
_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for InfluxDB."""

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN

    def __init__(self):
        """Initialize config flow."""
        self._data = None

    async def async_step_user(self, user_input=None):
        """Collect api version."""
        if user_input is not None:
            self._data = user_input
            return await self.async_step_connection()

        return self.async_show_form(
            step_id="user", data_schema=API_VERSION_SCHEMA, errors=None
        )


    async def async_step_connection(self, user_input=None):
        """Collect connection and authorization details."""
        errors = {}
        if user_input is not None:
            try:
                self._data.update(user_input)
                config = INFLUX_SCHEMA(self._data)
                influx = await self.hass.async_add_executor_job(
                    get_influx_connection, config, True, False
                )
            except ValueError:
                pass
            except ConnectionRefusedError as exc:
                _LOGGER.error(exc)
                if self._data[CONF_API_VERSION] == API_VERSION_2:
                    errors[CONF_TOKEN] = "write_error_token"
                else:
                    errors[CONF_USERNAME] = "write_error_basic"
            except ConnectionError as exc:
                _LOGGER.error(exc)
                errors["base"] = "connection_error"
            except Exception as exc: # pylint: disable=broad-except
                _LOGGER.error(exc)
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=f"InfluxDB ({config[CONF_HOST]})",
                    data=config,
                )

        schema = CONNECTION_SCHEMA_V2 if self._data[CONF_API_VERSION] == API_VERSION_2 else CONNECTION_SCHEMA_V1
        return self.async_show_form(
            step_id="connection", data_schema=schema, errors=errors
        )
