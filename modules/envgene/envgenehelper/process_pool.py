from concurrent.futures import ProcessPoolExecutor
from os import getenv

from envgene_shared.utils.logger import logger

_process_pool = None


def parallel_workers() -> int:
    return int(getenv("ENVGENE_PARALLEL_WORKERS", "0"))


def map_in_processes(function, tasks: list[tuple]) -> list:
    global _process_pool
    if parallel_workers() < 2 or len(tasks) < 2:
        return [function(*task) for task in tasks]
    if _process_pool is None:
        logger.info(f"Parallel workers: {parallel_workers()}")
        _process_pool = ProcessPoolExecutor(max_workers=parallel_workers())
    return list(_process_pool.map(function, *zip(*tasks)))
