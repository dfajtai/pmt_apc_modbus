import asyncio
import random
import time
from typing import Dict, Tuple, Callable, Any

from services.async_modbus_handler import AsyncModbusHandler
from services.modbus_query import ModbusQuery


class DummyAsyncModbusHandler(AsyncModbusHandler):
    """
    Dummy Modbus handler that simulates Modbus read/write operations.
    """

    # Hardcoded: the register that holds sampling status
    SAMPLING_STATUS_REGISTER = 30164
    SAMPLING_CONTROL_REGISTER = 2  # write_coil(target=2)

    def __init__(
        self,
        fixed: Dict[int, Any] = None,
        random_ranges: Dict[int, Tuple[int, int]] = None,
        counters: Dict[int, int] = None,
        generators: Dict[int, Callable[[], Any]] = None,
        delay: float = 0.0,
    ):
        super().__init__()

        self.fixed = fixed or {}
        self.random_ranges = random_ranges or {}
        self.counters = counters or {}
        self.generators = generators or {}
        self.delay = delay

        # internal state for write_coil/register
        self.written_values = {}

        # dynamic sampling status (default = fixed or NORMAL)
        self.sampling_status = self.fixed.get(self.SAMPLING_STATUS_REGISTER, 0)

    async def _simulate_delay(self):
        if self.delay > 0:
            await asyncio.sleep(self.delay)

    # ---------------------------
    # External control function
    # ---------------------------
    def set_sampling_status(self, value: int):
        """Allow external modification of sampling status."""
        self.sampling_status = int(value)

    # ---------------------------
    # Dummy value generator
    # ---------------------------
    def _get_dummy_value(self, query: ModbusQuery):
        reg = query.register

        # sampling status always comes from internal state, not from fixed[]
        if reg == self.SAMPLING_STATUS_REGISTER:
            return self.sampling_status

        # custom generators
        if reg in self.generators:
            return self.generators[reg]()

        # fixed
        if reg in self.fixed:
            return self.fixed[reg]

        # counters
        if reg in self.counters:
            self.counters[reg] += 1
            return self.counters[reg]

        # random ranges
        if reg in self.random_ranges:
            lo, hi = self.random_ranges[reg]
            return random.randint(lo, hi)

        return 0

    # ---------------------------
    # Overrides
    # ---------------------------
    async def read_input(self, query: ModbusQuery):
        await self._simulate_delay()
        return self._get_dummy_value(query)

    async def read_holding(self, query: ModbusQuery):
        await self._simulate_delay()
        return self._get_dummy_value(query)

    async def write_coil(self, query: ModbusQuery, value):
        await self._simulate_delay()
        reg = query.register

        # if coil #2 is written → change sampling status
        if reg == self.SAMPLING_CONTROL_REGISTER:
            self.sampling_status = 1 if value else 0

        self.written_values[reg] = value
        return True

    async def write_register(self, query: ModbusQuery, value):
        await self._simulate_delay()
        reg = query.register
        self.written_values[reg] = value
        return True



dummy = DummyAsyncModbusHandler(
    fixed={
        # 30164: 1,    # sampling status → SAMPLING
        30214: 0,    # device status → NORMAL
    },
    counters={
        30310: int(time.time()),  # timestamp (UINT32) increments each read
        # 30022: 100,         # flow rate counter (flow = 101, 102, 103...)
    },
    random_ranges={
        30312: (0, 50),   # pc1
        30314: (0, 10),   # pc2
        30316: (0, 2),   # pc3
    },
    delay=0.02   # optional artificial latency
)