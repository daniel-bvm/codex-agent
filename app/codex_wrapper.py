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
    providerFromEnv = os.getenv("CODEX_PROVIDER", "local")
    
    command = [
        "/workspace/anon-codex/codex-cli/dist/cli.js",
        "-p",
        providerFromEnv,
        "--auto-edit",
        "--full-auto",
        "--no-project-doc",
        "--dangerously-auto-approve-everything",
        "--json", "-q",
        prompt
    ]

    command_str = " ".join(f'{arg!r}' for arg in command)

    process = await asyncio.create_subprocess_shell(
        command_str,
        stdout=asyncio.subprocess.PIPE,
        stderr=sys.stderr,
        stdin=asyncio.subprocess.PIPE,
        env=os.environ
    )

    async for line in read_stream(process.stdout):

        try:
            line_json: dict = json.loads(line)
        except json.JSONDecodeError:
            print(f"Error decoding line: {line} (skipping)")
            continue

        yield create_model_from_dict(line_json)
