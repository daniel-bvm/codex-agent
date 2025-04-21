from typing import AsyncGenerator, Literal, Any
from .models import (
    BaseResponse, 
    FunctionCallOutputResponse, 
    FunctionCallResponse, 
    ReasoningResponse,
    MessageResponse,
    ChatCompletionStreamResponse,
    random_uuid
)
from .codex_wrapper import run_codex
import time
import json

async def wrap_chunk(uuid: str, raw: str) -> ChatCompletionStreamResponse:
    return ChatCompletionStreamResponse(
        id=uuid,
        object='chat.completion.chunk',
        created=int(time.time()),
        model='unspecified',
        choices=[
            dict(
                index=0,
                delta=dict(content=raw)
            )
        ]
    )
    

async def wrap_toolcall_request(uuid: str, fn_name: str, args: dict[str, Any]) -> ChatCompletionStreamResponse:
    args_str = json.dumps(args, indent=2)
    
    template = f'''
Executing <b>{fn_name}</b>

<details>
<summary>
Arguments:
</summary>

```json
{args_str}
```

</details>
'''

    return ChatCompletionStreamResponse(
        id=uuid,
        object='chat.completion.chunk',
        created=int(time.time()),
        model='unspecified',
        choices=[
            dict(
                index=0,
                delta=dict(
                    content=template,
                    role='tool'
                ),
            )
        ]
    )


async def wrap_toolcall_response(uuid: str, fn_name: str, args: dict[str, Any], result: Any) -> ChatCompletionStreamResponse:
    result_str = json.dumps(result, indent=2)

    result = f'''
<details>
<summary>
Response:
</summary>

```json
{result_str}
```

</details>
<br>

'''
    
    return ChatCompletionStreamResponse(
        id=uuid,
        object='chat.completion.chunk',
        created=int(time.time()),
        model='unspecified',
        choices=[
            dict(
                index=0,
                delta=dict(
                    content=result, 
                    role='tool'
                ),
            )
        ]
    )

async def to_chunk_data(chunk: ChatCompletionStreamResponse) -> bytes:
    return ("data: " + json.dumps(chunk.model_dump()) + "\n\n").encode()

async def prompt(messages: list[dict[str, Any]], *args, **kwargs) -> AsyncGenerator[bytes, None]:
    prompt = messages[-1]["content"]
    response_id = random_uuid()
    identities = set([])

    async for item in run_codex(prompt):
        _id = item.id

        if _id not in identities:
            identities.add(_id)
        else:
            continue

        if isinstance(item, FunctionCallResponse):
            yield await to_chunk_data(await wrap_toolcall_request(response_id, item.name, item.arguments))
        elif isinstance(item, FunctionCallOutputResponse):
            yield await to_chunk_data(await wrap_toolcall_response(response_id, 'something', {}, item.output))
        elif isinstance(item, MessageResponse):
            for content in item.content:
                if content.type == "output_text":
                    yield await to_chunk_data(await wrap_chunk(response_id, content.text))

        # elif isinstance(item, ReasoningResponse):
        #     if item.duration_ms > 0:
        #         yield await to_chunk_data(await wrap_chunk(response_id, f"> Thinking in {item.duration_ms / 1000} seconds\n\n"))
