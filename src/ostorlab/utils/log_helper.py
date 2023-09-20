from dataclasses import dataclass


@dataclass
class CpuInfo:
    load: list[float] | float


@dataclass
class MemoryInfo:
    total: int
    available: int
    used: int
    percent: float


@dataclass
class StorageInfo:
    total: int
    used: int
    free: int


@dataclass
class SystemLoadInfo:
    cpu_load: CpuInfo
    memory_usage: MemoryInfo
    storage: StorageInfo

    def __str__(self):
        return (
            f"CPU Load: {self.cpu_load.load}\n"
            f"Memory Usage: Total={self.memory_usage.total}, "
            f"Available={self.memory_usage.available}, "
            f"Used={self.memory_usage.used}, "
            f"Percent={self.memory_usage.percent}\n"
            f"Storage: Total={self.storage.total}, "
            f"Used={self.storage.used}, "
            f"Free={self.storage.free}"
        )


def get_system_load() -> SystemLoadInfo | None:
    """Get system load information.
    We use psutil to get the system load information. in case psutil is not available, we return None.
    Returns:
        System load information or None.
    """
    try:
        import psutil

        # Get CPU load information
        cpu_info = CpuInfo(psutil.cpu_percent(interval=None, percpu=True))

        # Get memory usage information
        memory_info = psutil.virtual_memory()
        memory_info = MemoryInfo(
            total=memory_info.total,
            available=memory_info.available,
            used=memory_info.used,
            percent=memory_info.percent,
        )

        # Get storage information
        partitions = psutil.disk_partitions()
        total_storage, used_storage, free_storage = 0, 0, 0
        for partition in partitions:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            total_storage += partition_usage.total
            used_storage += partition_usage.used
            free_storage += partition_usage.free
        storage_info = StorageInfo(
            total=total_storage, used=used_storage, free=free_storage
        )

        # Create the SystemLoadInfo data class instance
        return SystemLoadInfo(
            cpu_load=cpu_info, memory_usage=memory_info, storage=storage_info
        )

    except ImportError:
        # psutil is not available, return None
        return None
