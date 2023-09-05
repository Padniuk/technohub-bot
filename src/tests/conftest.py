import pytest
from aiogram.fsm.storage.memory import MemoryStorage

@pytest.fixture(scope='session')
async def memory_storage():
    storage = MemoryStorage()
    try:
        yield storage
    finally:
        await storage.close()