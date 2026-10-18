from core.generations import NixGenerationManager, GenerationInfo
from core.command_executor import AsyncCommandExecutor, CommandResult


class MockExecutor(AsyncCommandExecutor):
    async def run(self, cmd, **kwargs):
        if "list-generations" in cmd:
            mock_output = (
                "  1   2026-10-18 20:30:00\n"
                "  2   2026-10-18 21:00:00\n"
                "  3   2026-10-18 22:15:30   (current)\n"
            )
            return CommandResult(stdout=mock_output, stderr="", returncode=0)
        return CommandResult(stdout="", stderr="", returncode=0)


import pytest

@pytest.mark.asyncio
async def test_parse_generations_list():
    mgr = NixGenerationManager(MockExecutor())
    gens = await mgr.list_generations()

    assert len(gens) == 3
    # Sorted reverse by id
    assert gens[0].id == 3
    assert gens[0].is_current is True
    assert gens[1].id == 2
    assert gens[1].is_current is False
    assert gens[2].id == 1
