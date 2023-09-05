import pytest
from unittest.mock import AsyncMock
from bot.handlers.users import help

@pytest.mark.asyncio
async def test_start_handler():
    message = AsyncMock()
    await help(message)

    message.answer.assert_called_with("Для створення посту введість команду:\n `/post`", parse_mode='Markdown')
