from typing import TYPE_CHECKING, Any, Dict, Optional, List, Coroutine

from scrapli import AsyncScrapli
from scrapli.driver import AsyncGenericDriver
from scrapli.exceptions import ScrapliModuleNotFound
from scrapli_netconf.driver import AsyncNetconfDriver

from nornir.core.configuration import Config
from nornir.core.task import Task

if TYPE_CHECKING:
    from nornir.core.plugins.connections import (
        ConnectionPlugin,
    )  # pylint: disable=C0412

CONNECTION_NAME = "scrapli"

PLATFORM_MAP = {
    "ios": "cisco_iosxe",
    "nxos": "cisco_nxos",
    "iosxr": "cisco_iosxr",
    "eos": "arista_eos",
    "junos": "juniper_junos",
}


class AsyncScrapliCore:
    """Scrapli connection plugin for nornir"""

    async def open(  # pylint: disable=R0917
        self,
        hostname: Optional[str],
        username: Optional[str],
        password: Optional[str],
        port: Optional[int],
        platform: Optional[str],
        extras: Optional[Dict[str, Any]] = None,
        configuration: Optional[Config] = None,
    ) -> None:
        """
        Open a scrapli connection to a device

        Args:
            hostname: hostname from nornir inventory
            username: username from nornir inventory/connection_options for scrapli
            password: password from nornir inventory/connection_options for scrapli
            port: port from nornir inventory/connection_options for scrapli
            platform: platform from nornir inventory/connection_options for scrapli
            extras: extras dict from connection_options for scrapli -- pass all other scrapli
                arguments here
            configuration: nornir configuration

        Returns:
            None

        Raises:
            NornirScrapliInvalidPlatform: if no platform or an invalid scrapli/napalm platform
                string is provided

        """
        extras = extras or {}
        # 99.9% configuration will always be passed here... but to be consistent w/ the other
        # plugins we'll leave the function signature same/same as the others
        global_config = configuration.dict() if configuration else {}

        parameters: Dict[str, Any] = {
            "host": hostname,
            "auth_username": username or "",
            "auth_password": password or "",
            "port": port or 22,
            "ssh_config_file": global_config.get("ssh", {}).get("config_file", False),
        }

        # will override any of the configs from global nornir config (such as ssh config file) with
        # options from "extras" (connection options)
        parameters.update(extras)

        if extras.get("channel_log", False) is True:
            # if channel_log value is just "True" we append the hostname so that we don't have a
            # single file for potentially hundreds (or more!) of devices which obviously won't
            # work very well. don't update the extras dict directly as that is probably coming from
            # group/default vars, so just push this right onto the new parameters' dict.
            parameters.update({"channel_log": f"scrapli_channel_{hostname}.log"})

        if not platform:
            raise ValueError(
                f"'platform' not provided in inventory for host `{hostname}`"
            )

        final_platform: str = PLATFORM_MAP.get(platform, platform)

        if final_platform == "generic":
            connection = AsyncGenericDriver(**parameters)
        else:
            try:
                connection = AsyncScrapli(**parameters, platform=final_platform)
            except ScrapliModuleNotFound as exc:
                raise ValueError(
                    f"Provided platform `{final_platform}` is not a valid scrapli or napalm "
                    "platform, or is not a valid scrapli-community platform."
                ) from exc

        await connection.open()
        self.connection = connection  # pylint: disable=W0201

    async def close(self) -> None:
        """
        Close a scrapli connection to a device

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self.connection.close()


class ScrapliNetconf:
    """Scrapli NETCONF connection plugin for nornir"""

    async def open(  # pylint: disable=R0917
        self,
        hostname: Optional[str],
        username: Optional[str],
        password: Optional[str],
        port: Optional[int],
        platform: Optional[str],
        extras: Optional[Dict[str, Any]] = None,
        configuration: Optional[Config] = None,
    ) -> None:
        """
        Open a scrapli connection to a device

        Args:
            hostname: hostname from nornir inventory
            username: username from nornir inventory/connection_options for scrapli
            password: password from nornir inventory/connection_options for scrapli
            port: port from nornir inventory/connection_options for scrapli
            platform: platform from nornir inventory/connection_options for scrapli; ignored with
                scrapli netconf
            extras: extras dict from connection_options for scrapli -- pass all other scrapli
                arguments here
            configuration: nornir configuration

        Returns:
            None

        Raises:
            N/A

        """
        # platform is irrelevant for scrapli netconf for now
        _ = platform
        extras = extras or {}
        # 99.9% configuration will always be passed here... but to be consistent w/ the other
        # plugins we'll leave the function signature same/same as the others
        global_config = configuration.dict() if configuration else {}

        parameters: Dict[str, Any] = {
            "host": hostname,
            "auth_username": username or "",
            "auth_password": password or "",
            "port": port or 830,
            "ssh_config_file": global_config.get("ssh", {}).get("config_file", False),
        }

        # will override any of the configs from global nornir config (such as ssh config file) with
        # options from "extras" (connection options)
        parameters.update(extras)

        connection = AsyncNetconfDriver(**parameters)
        await connection.open()
        self.connection = connection  # pylint: disable=W0201

    async def close(self) -> None:
        """
        Close a scrapli netconf connection to a device

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        await self.connection.close()
