"""The netgear component."""
import logging
from concurrent.futures import ProcessPoolExecutor
import asyncio
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pynetgear_enhanced import NetgearEnhanced as Netgear

from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    DOMAIN,
    TEST_TIMEOUT,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "device_tracker"]


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up configured Netgear."""
    hass.data.setdefault(DOMAIN, {})
    return True


def _api_in_executor(loop, api):
    """Try login in executor so it is async."""
    ex = ProcessPoolExecutor(2)
    yield from loop.run_in_executor(ex, api)


def _run_with_timeout(loop, api, timeout=TEST_TIMEOUT):
    """Run a Netgear API with a timeout."""
    return loop.run_until_complete(
        asyncio.wait_for(_api_in_execution(loop, api), timeout)
    )


def get_connection(loop, config, test=False):
    """Test connection to Netgear router."""
    netgear = Netgear(
        ssl=user_input[CONF_SSL],
        host=user_input[CONF_HOST],
        port=user_input[CONF_PORT],
        user=user_input[CONF_USERNAME],
        password=user_input[CONF_PASSWORD],
    )
    if test:
        return netgear, _run_with_timeout(loop, netgear.login)

    return netgear


async def async_setup_entry(hass, config_entry) -> bool:
    """Set up Netgear as config entry."""
    netgear = get_connection(hass.loop, config_entry.data)

    coordinator = NetgearDataUpdateCoordinator(hass, netgear)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = config_entry.add_update_listener(update_listener)

    hass.data[DOMAIN][config_entry.entry_id] = {
        COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, component)
                for component in PLATFORMS
            ]
        )
    )

    hass.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(hass, config_entry):
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class NetgearDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Netgear data API."""

    def __init__(self, hass, netgear):
        """Initialize."""
        self.netgear = netgear
        _LOGGER.debug("Data will be update every %s", UPDATE_INTERVAL)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            success = _run_with_timeout(hass.loop self.netgear.login, 5)
            if success == True:
                return {
                    **_api_in_executor(hass.loop, self.netgear.get_block_device_enable_status),
                    **_api_in_executor(hass.loop, self.netgear.get_traffic_meter_statistics),
                    **_api_in_executor(hass.loop, self.netgear.get_traffic_meter_enabled),
                    **_api_in_executor(hass.loop, self.netgear.get_traffic_meter_options),
                    **_api_in_executor(hass.loop, self.netgear.get_parental_control_enable_status),
                    **_api_in_executor(hass.loop, self.netgear.get_all_mac_addresses),
                    **_api_in_executor(hass.loop, self.netgear.get_dns_masq_device_id),
                    **_api_in_executor(hass.loop, self.netgear.get_info),
                    **_api_in_executor(hass.loop, self.netgear.get_support_feature_list_XML),
                    **_api_in_executor(hass.loop, self.netgear.get_qos_enable_status),
                    **_api_in_executor(hass.loop, self.netgear.get_bandwidth_control_options),
                    **_api_in_executor(hass.loop, self.netgear.get_guest_access_enabled),
                    **_api_in_executor(hass.loop, self.netgear.get_5g_guest_access_enabled),
                    **_api_in_executor(hass.loop, self.netgear.get_2g_info),
                    **_api_in_executor(hass.loop, self.netgear.get_5g_info),
                    **_api_in_executor(hass.loop, self.netgear.get_guest_access_network_info),
                    **_api_in_executor(hass.loop, self.netgear.get_5g_guest_access_network_info),
                    **_api_in_executor(hass.loop, self.netgear.check_new_firmware, 20),
                }

            raise UpdateFailed("Check config, couldn't connect with Netgear router")
        except asyncio.exceptions.TimeoutError as error:
            raise UpdateFailed(error) from error
