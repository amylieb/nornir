from concurrent.futures import ThreadPoolExecutor
from typing import List

import asyncio
from aiomultiprocess import Pool

from nornir.core.inventory import Host
from nornir.core.task import AggregatedResult, Task, AsyncTask
from nornir.core.exceptions import AsyncError


class SerialRunner:
    """
    SerialRunner runs the task over each host one after the other without any parellelization
    """

    def __init__(self) -> None:
        pass

    def run(self, task: Task, hosts: List[Host]) -> AggregatedResult:
        result = AggregatedResult(task.name)
        for host in hosts:
            result[host.name] = task.copy().start(host)
        return result


class ThreadedRunner:
    """
    ThreadedRunner runs the task over each host using threads

    Arguments:
        num_workers: number of threads to use
    """

    def __init__(self, num_workers: int = 20) -> None:
        self.num_workers = num_workers

    def run(self, task: Task, hosts: List[Host]) -> AggregatedResult:
        result = AggregatedResult(task.name)
        futures = []
        with ThreadPoolExecutor(self.num_workers) as pool:
            for host in hosts:
                future = pool.submit(task.copy().start, host)
                futures.append(future)

        for future in futures:
            worker_result = future.result()
            result[worker_result.host.name] = worker_result
        return result


class AsyncRunner:
    """
    Runs tasks in a single async loop. Allows for 'chunking' the
    hosts.
    """

    def __init__(self, chunk_size=30) -> None:
        self.chunk_size = chunk_size

    async def run(self, task: AsyncTask, hosts: List[Host]) -> AggregatedResult:

        if not isinstance(task, AsyncTask):
            raise AsyncError(
                f"{task.name} must be an AsyncTask to run in an async runner"
            )

        result = AggregatedResult(task.name)
        for i in range(0, len(hosts), self.chunk_size):

            host_chunk = [h for h in list(hosts)[i : i + self.chunk_size]]
            async_result = await asyncio.gather(
                *[task.copy().start(h) for h in host_chunk]
            )

            for host, idx in zip(host_chunk, range(0, self.chunk_size)):
                result[host.name] = async_result[idx]

        return result


class AsyncMultiRunner:
    """
    Run tasks in multiple processes with aiomultiprocess
    """

    def __init__(self, chunk_size=20, num_workers=None) -> None:
        self.chunk_size = chunk_size
        self.num_workers = num_workers

    async def run(self, task: AsyncTask, hosts: List[Host]) -> AggregatedResult:

        if not isinstance(task, AsyncTask):
            raise AsyncError(
                f"{task.name} must be an AsyncTask to run in an async runner"
            )

        result = AggregatedResult(task.name)

        async with Pool(
            processes=self.num_workers, childconcurrency=self.chunk_size
        ) as pool:
            async_result = await asyncio.gather(
                *[pool.apply(task.copy().start, h) for h in hosts]
            )

        for host, idx in zip(hosts, range(0, len(hosts))):
            result[host.name] = async_result[idx]
        return result
