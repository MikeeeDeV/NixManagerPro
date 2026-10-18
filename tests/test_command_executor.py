import asyncio
import pytest
from core.command_executor import AsyncCommandExecutor, CommandError, CommandResult


@pytest.mark.asyncio
async def test_successful_command_execution():
    executor = AsyncCommandExecutor()
    result = await executor.run(["echo", "hello world"])
    assert result.returncode == 0
    assert "hello world" in result.stdout
    assert bool(result) is True


@pytest.mark.asyncio
async def test_command_streaming_callback():
    executor = AsyncCommandExecutor()
    captured = []

    def callback(stream, line):
        captured.append((stream, line))

    executor.set_output_callback(callback)
    await executor.run(["echo", "line1\nline2"])

    lines = [c[1] for c in captured]
    assert any("line1" in l for l in lines)


@pytest.mark.asyncio
async def test_failed_command_raises_error():
    executor = AsyncCommandExecutor()
    with pytest.raises(CommandError) as exc_info:
        await executor.run(["false"])
    assert "Command failed" in str(exc_info.value)
