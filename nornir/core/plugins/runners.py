from typing import Any, List, Protocol, Type

from nornir.core.inventory import Host
from nornir.core.plugins.register import PluginRegister
from nornir.core.task import AggregatedResult, Task

import asyncio


RUNNERS_PLUGIN_PATH = "nornir.plugins.runners"


class RunnerPlugin(Protocol):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        This method configures the plugin
        """
        raise NotImplementedError("needs to be implemented by the plugin")

    def run(self, task: Task, hosts: List[Host]) -> AggregatedResult:
        """
        This method runs the given task over all the hosts
        """
        raise NotImplementedError("needs to be implemented by the plugin")


class AsyncRunnerPlugin(asyncio.Protocol):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        This method configures the plugin
        """
        raise NotImplementedError("needs to be implemented by the plugin")

    async def run(self, task: Task, hosts: List[Host]) -> AggregatedResult:
        """
        This method runs the given task over all the hosts
        """
        raise NotImplementedError("needs to be implemented by the plugin")


RunnersPluginRegister: PluginRegister[Type[RunnerPlugin]] = PluginRegister(
    RUNNERS_PLUGIN_PATH
)
AsyncRunnersPluginRegister: PluginRegister[Type[AsyncRunnerPlugin]] = PluginRegister(
    RUNNERS_PLUGIN_PATH
)
