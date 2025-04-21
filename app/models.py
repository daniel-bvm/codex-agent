from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Any, Literal, Union, Optional, ClassVar
import json
import uuid
import time

class BaseResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["message", "function_call", "reasoning", "function_call_output", "output_text", "input_text"]
    status: Literal["completed"] = Field(default="completed")

class ReasoningResponse(BaseResponse):
    summary: list[Any] = Field(default_factory=list)
    duration_ms: int = Field(default=0)

class FunctionCallResponse(BaseResponse):
    arguments: dict[str, Any]
    call_id: str
    name: str
    
    @model_validator(mode="before")
    def validate_arguments(cls, data: dict) -> dict:
        if "arguments" in data and isinstance(data["arguments"], str):
            data["arguments"] = json.loads(data["arguments"])
        return data
    
class FunctionCallOutputResponse(BaseResponse):
    output: Union[str, dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)
    call_id: str
    
    @model_validator(mode="before")
    def validate_output(cls, data: dict) -> dict:
        if "output" in data and isinstance(data["output"], str):
            data["output"] = json.loads(data["output"])
        return data


class ContentPart(BaseResponse):
    type: Literal["input_text", "output_text"]
    text: str
    
class MessageResponse(BaseResponse):
    content: list[ContentPart]
    role: Literal["user", "assistant", "tool", "system"]

def create_model_from_dict(data: dict) -> BaseModel:
    if data["type"] == "message":
        return MessageResponse(**data)
    
    if data["type"] == "function_call":
        return FunctionCallResponse(**data)
    
    if data["type"] == "reasoning":
        return ReasoningResponse(**data)
    
    if data["type"] == "function_call_output":
        return FunctionCallOutputResponse(**data)

    return None


class OpenAIBaseModel(BaseModel):
    # OpenAI API does allow extra fields
    model_config = ConfigDict(extra="allow")

    # Cache class field names
    field_names: ClassVar[Optional[set[str]]] = None

    @model_validator(mode="wrap")
    @classmethod
    def __log_extra_fields__(cls, data, handler):
        result = handler(data)
        if not isinstance(data, dict):
            return result
        field_names = cls.field_names
        if field_names is None:
            # Get all class field names and their potential aliases
            field_names = set()
            for field_name, field in cls.model_fields.items():
                field_names.add(field_name)
                if alias := getattr(field, "alias", None):
                    field_names.add(alias)
            cls.field_names = field_names

        return result
    
class ChatCompletionLogProb(OpenAIBaseModel):
    token: str
    logprob: float = -9999.0
    bytes: Optional[list[int]] = None

class ChatCompletionLogProbsContent(ChatCompletionLogProb):
    # Workaround: redefine fields name cache so that it's not
    # shared with the super class.
    field_names: ClassVar[Optional[set[str]]] = None
    top_logprobs: list[ChatCompletionLogProb] = Field(default_factory=list)

class ChatCompletionLogProbs(OpenAIBaseModel):
    content: Optional[list[ChatCompletionLogProbsContent]] = None


class DeltaFunctionCall(BaseModel):
    name: Optional[str] = None
    arguments: Optional[str] = None


def random_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())

# a tool call delta where everything is optional
class DeltaToolCall(OpenAIBaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-tool-{random_uuid()}")
    type: Literal["function"] = "function"
    index: int = Field(default_factory=lambda: -1)
    function: Optional[DeltaFunctionCall] = None

class DeltaMessage(OpenAIBaseModel):
    role: Optional[str] = None
    content: Optional[str] = None
    reasoning_content: Optional[str] = None
    tool_calls: list[DeltaToolCall] = Field(default_factory=list)


class ChatCompletionResponseStreamChoice(OpenAIBaseModel):
    index: int
    delta: DeltaMessage
    logprobs: Optional[ChatCompletionLogProbs] = None
    finish_reason: Optional[str] = None
    stop_reason: Optional[Union[int, str]] = None
    
class PromptTokenUsageInfo(OpenAIBaseModel):
    cached_tokens: Optional[int] = None

    
class UsageInfo(OpenAIBaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0
    completion_tokens: Optional[int] = 0
    prompt_tokens_details: Optional[PromptTokenUsageInfo] = None


class ChatCompletionStreamResponse(OpenAIBaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{random_uuid()}")
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[ChatCompletionResponseStreamChoice]
    usage: Optional[UsageInfo] = Field(default=None)
