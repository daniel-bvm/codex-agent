import asyncio
import os, sys
from typing import AsyncGenerator
import json
from .models import (
    create_model_from_dict,
    BaseResponse
)

async def read_stream(stream: asyncio.StreamReader) -> AsyncGenerator[str, None]:
    while True:
        line = await stream.readline()

        if not line:
            break

        yield line.decode(errors='ignore')

async def run_codex(prompt: str) -> AsyncGenerator[BaseResponse, None]:

    command = [
        "codex",
        "--auto-edit",
        "--full-auto",
        "--no-project-doc",
        "--json", "-q",
        prompt
    ]

    command_str = " ".join(f'{arg!r}' for arg in command)

    process = await asyncio.create_subprocess_shell(
        command_str,
        stdout=asyncio.subprocess.PIPE,
        stderr=sys.stderr,
        env=os.environ
    )

    async for line in read_stream(process.stdout):
        line_json: dict = json.loads(line)
        print(line_json)
        yield create_model_from_dict(line_json)
