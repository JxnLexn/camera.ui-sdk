from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Literal, NotRequired, Protocol, TypedDict, runtime_checkable


class AssistantModelSpec(TypedDict):
    """One model a plugin offers to the assistant. The user picks it under
    Settings, Assistant like any other model; the host never sees a key or an
    endpoint of it.

    Example:
        ```python
        on_device: AssistantModelSpec = {
            "id": "apple-on-device",
            "name": "Apple on-device",
            "contextTokens": 8192,
            "vision": True,
            "toolCalling": True,
            "structuredOutput": True,
            "note": "Runs on this Mac, nothing leaves the house.",
        }
        ```
    """

    id: str
    """Model id, unique within the plugin and stable across restarts: the settings store it."""

    name: str
    """Name shown in the model list."""

    contextTokens: int
    """Hard context limit of the model in tokens. The host plans prompt, tools and history with it."""

    vision: bool
    """The model reads images. Without it the host sends text only."""

    toolCalling: bool
    """The model calls tools. Without it the assistant answers from the conversation alone."""

    structuredOutput: bool
    """The model honors a JSON schema. Without it the host asks for free text and parses defensively."""

    toolRouting: NotRequired[bool]
    """The host picks the tools for a question with a short call of its own and puts only
    those in front of the model. For a small model that calls the tools it sees but
    does not work through a catalog of fifty."""

    note: NotRequired[str]
    """One line shown next to the model, for example where it runs or what it costs."""


class AssistantModelText(TypedDict):
    """Text part of a message."""

    type: Literal["text"]
    """Always ``text``."""

    text: str
    """The text itself."""


class AssistantModelImage(TypedDict):
    """Image part of a message. Arrives only for a model whose spec says
    ``vision``, and only when the instance allows pictures to reach the model."""

    type: Literal["image"]
    """Always ``image``."""

    data: str
    """Base64-encoded image bytes."""

    mimeType: Literal["image/jpeg", "image/png", "image/webp"]
    """MIME type of ``data``."""


AssistantModelContent = AssistantModelText | AssistantModelImage
"""Part of a message: text or an image."""


class AssistantModelToolCall(TypedDict):
    """A tool call: which tool with which arguments."""

    id: str
    """Id the host uses to match the result, unique within the request."""

    name: str
    """Name of the tool as declared in ``AssistantModelRequest["tools"]``."""

    arguments: dict[str, Any]
    """Arguments as parsed JSON, matching the tool's input schema."""


class AssistantModelMessage(TypedDict):
    """One message of the conversation. ``tool`` messages carry the result of
    the call with the matching ``toolCallId``."""

    role: Literal["user", "assistant", "tool"]
    """Who wrote it."""

    content: list[AssistantModelContent]
    """Text and images of the message."""

    toolCalls: NotRequired[list[AssistantModelToolCall]]
    """Tool calls the assistant asked for, on ``assistant`` messages."""

    toolCallId: NotRequired[str]
    """Call this message answers, on ``tool`` messages."""


class AssistantModelTool(TypedDict):
    """A tool the model may call in this request."""

    name: str
    """Name the model uses in its call."""

    description: str
    """What the tool does, written for the model."""

    inputSchema: dict[str, Any]
    """JSON Schema object of the arguments."""


class AssistantModelRequest(TypedDict):
    """One request to a plugin model: the conversation so far plus what the
    model may do with it."""

    modelId: str
    """Model id from ``AssistantModelSpec["id"]``."""

    system: list[str]
    """Instructions that precede the conversation."""

    messages: list[AssistantModelMessage]
    """The conversation, oldest first. The host has already trimmed it to ``contextTokens``."""

    tools: list[AssistantModelTool]
    """Tools the model may call. Empty when the run allows none."""

    outputSchema: NotRequired[dict[str, Any]]
    """JSON Schema the answer has to match. Only set for models whose spec says ``structuredOutput``."""

    maxOutputTokens: NotRequired[int]
    """Upper bound for the answer in tokens, when the host has one."""


class AssistantModelTextChunk(TypedDict):
    """A piece of the answer text."""

    type: Literal["text"]
    """Always ``text``."""

    delta: str
    """The text generated since the last chunk."""


class AssistantModelToolCallChunk(TypedDict):
    """A tool call the model asks for, with complete arguments."""

    type: Literal["tool_call"]
    """Always ``tool_call``."""

    call: AssistantModelToolCall
    """The call itself."""


class AssistantModelUsageChunk(TypedDict):
    """What the answer consumed."""

    type: Literal["usage"]
    """Always ``usage``."""

    promptTokens: int
    """Tokens the request consumed."""

    completionTokens: int
    """Tokens the answer consumed."""


class AssistantModelDoneChunk(TypedDict):
    """End of the answer, yielded exactly once."""

    type: Literal["done"]
    """Always ``done``."""

    finish: Literal["stop", "tool_calls", "length", "error"]
    """Why the model stopped."""

    message: NotRequired[str]
    """What went wrong, with ``error``."""


AssistantModelChunk = (
    AssistantModelTextChunk | AssistantModelToolCallChunk | AssistantModelUsageChunk | AssistantModelDoneChunk
)
"""A piece of the answer: text, a tool call, token counts, or the end."""


class AssistantModelStatus(TypedDict):
    """Whether the plugin can answer right now. A model that has to be
    downloaded or loaded first reports ``ready: False`` with a line the settings
    page shows, and a ``progress`` while it knows one.

    Example:
        ```python
        {"ready": False, "message": "macOS is downloading the model", "progress": 0.62}
        ```
    """

    ready: bool
    """The models of this plugin can answer right now."""

    message: NotRequired[str]
    """One line for the user: what the plugin is waiting for, or what it is doing."""

    progress: NotRequired[float]
    """How far the loading got, between 0 and 1."""


class AssistantModelContext(TypedDict):
    """Who the answer is for and when to stop writing it."""

    userId: NotRequired[str]
    """ID of the user the answer is for. Absent for scheduled runs and plugin requests."""

    language: str
    """BCP 47 language tag the answer should use."""

    timeoutMs: int
    """Milliseconds the host waits before it drops the answer."""


@runtime_checkable
class AssistantModelProvider(Protocol):
    """Implemented by plugins that list ``PluginInterface.AssistantModels`` in
    their contract. Such a plugin is a bridge to a model the host cannot reach
    itself: one without an HTTP API, one behind an unusual authentication, or
    one that lives on the machine the plugin runs on. The plugin holds no
    conversation state, every request carries the whole conversation.

    Example:
        ```python
        class ApplePlugin(BasePlugin):
            async def assistantModels(self) -> list[AssistantModelSpec]:
                return [
                    {
                        "id": "apple-on-device",
                        "name": "Apple on-device",
                        "contextTokens": 8192,
                        "vision": True,
                        "toolCalling": True,
                        "structuredOutput": True,
                    }
                ]

            async def assistantGenerate(
                self, request: AssistantModelRequest, ctx: AssistantModelContext
            ) -> AsyncIterator[AssistantModelChunk]:
                async for delta in self.session.stream(request, ctx["timeoutMs"]):
                    yield {"type": "text", "delta": delta}
                yield {"type": "done", "finish": "stop"}
        ```
    """

    async def assistantModels(self) -> list[AssistantModelSpec]:
        """List the models this plugin offers. Called after the plugin is ready
        and whenever the settings page is opened.

        Returns:
            The specs, empty while the plugin has no usable model (no hardware,
            no permission yet).
        """
        ...

    async def assistantModelStatus(self) -> AssistantModelStatus:
        """Report whether the models can answer right now. The host asks before
        it offers them and while the settings page is open, so a model that is
        still downloading shows up as busy instead of missing. Leave it out when
        the models are usable as soon as the plugin runs.

        Returns:
            Readiness, with a line and a progress while it loads.
        """
        ...

    def assistantGenerate(
        self, request: AssistantModelRequest, ctx: AssistantModelContext
    ) -> AsyncIterator[AssistantModelChunk]:
        """Answer one request. The host reads chunks until ``done``, then either
        returns the text to the user or runs the tool calls and asks again with
        their results in ``messages``.

        Args:
            request: Conversation, tools and schema for this answer.
            ctx: Who asks, in which language, and how long the host waits.

        Returns:
            The answer in pieces.
        """
        ...
