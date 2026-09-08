from __future__ import annotations

from typing import Any, Literal, NotRequired, Protocol, TypedDict, runtime_checkable


class AssistantToolStringProperty(TypedDict):
    """String argument of a tool input."""

    type: Literal["string"]
    """Always ``string``."""

    description: NotRequired[str]
    """What the argument means, written for the model."""

    enum: NotRequired[list[str]]
    """Allowed values."""

    format: NotRequired[Literal["date-time", "date", "time"]]
    """Expected text format."""


class AssistantToolNumberProperty(TypedDict):
    """Numeric argument of a tool input."""

    type: Literal["number", "integer"]
    """``number`` or ``integer``."""

    description: NotRequired[str]
    """What the argument means, written for the model."""

    minimum: NotRequired[float]
    """Smallest allowed value."""

    maximum: NotRequired[float]
    """Largest allowed value."""


class AssistantToolBooleanProperty(TypedDict):
    """Boolean argument of a tool input."""

    type: Literal["boolean"]
    """Always ``boolean``."""

    description: NotRequired[str]
    """What the argument means, written for the model."""


class AssistantToolArrayProperty(TypedDict):
    """Array argument of a tool input."""

    type: Literal["array"]
    """Always ``array``."""

    items: AssistantToolProperty
    """Schema of each element."""

    description: NotRequired[str]
    """What the argument means, written for the model."""

    minItems: NotRequired[int]
    """Fewest elements allowed."""

    maxItems: NotRequired[int]
    """Most elements allowed."""


class AssistantToolObjectProperty(TypedDict):
    """Object argument of a tool input."""

    type: Literal["object"]
    """Always ``object``."""

    properties: dict[str, AssistantToolProperty]
    """Named members of the object."""

    description: NotRequired[str]
    """What the argument means, written for the model."""

    required: NotRequired[list[str]]
    """Members the model has to provide."""


AssistantToolProperty = (
    AssistantToolStringProperty
    | AssistantToolNumberProperty
    | AssistantToolBooleanProperty
    | AssistantToolArrayProperty
    | AssistantToolObjectProperty
)
"""Property schema of a tool input: the JSON Schema draft-07 subset every
supported model provider accepts unchanged."""


class AssistantToolSchema(TypedDict):
    """Input schema of a tool: always an object schema. The model fills the
    properties, the host passes them to ``callAssistantTool`` as parsed JSON."""

    type: Literal["object"]
    """Always ``object``."""

    properties: dict[str, AssistantToolProperty]
    """Named arguments the model may pass."""

    required: NotRequired[list[str]]
    """Arguments the model has to provide."""

    additionalProperties: NotRequired[Literal[False]]
    """Set to ``False`` to reject arguments outside ``properties``."""


class AssistantToolSpec(TypedDict):
    """One tool a plugin offers to the assistant. The host prefixes ``name``
    with the plugin name, so names only have to be unique within the plugin.

    Example:
        ```python
        query_events = define_assistant_tool(
            {
                "name": "query_events",
                "description": "List recorded events for a time range, optionally filtered by camera and label.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "from": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Start of the range, ISO 8601",
                        },
                        "to": {
                            "type": "string",
                            "format": "date-time",
                            "description": "End of the range, ISO 8601",
                        },
                        "camera": {"type": "string", "description": "Camera name, all cameras when omitted"},
                    },
                    "required": ["from", "to"],
                },
            }
        )
        ```
    """

    name: str
    """Tool name in snake_case, unique within the plugin."""

    description: str
    """What the tool does and when to use it, written for the model. One or two sentences, name units and defaults."""

    inputSchema: AssistantToolSchema
    """Object schema of the arguments (see :class:`AssistantToolSchema`)."""

    approval: NotRequired[bool]
    """The user confirms every call before it runs. Set it on anything that changes state."""

    adminOnly: NotRequired[bool]
    """Hidden from users without the admin role."""

    timeoutMs: NotRequired[int]
    """Time the host waits for ``callAssistantTool``, in milliseconds. Default 60000."""

    lazy: NotRequired[bool]
    """Offered through tool discovery instead of on every turn. Use for rarely needed tools."""


class AssistantToolContext(TypedDict):
    """Who is asking and in which language. Passed to every tool call; the host
    has already enforced ``adminOnly`` and ``approval``, the fields are
    information."""

    userId: str
    """ID of the user talking to the assistant."""

    role: Literal["user", "admin", "master"]
    """Role of the user."""

    language: str
    """BCP 47 language tag of the conversation, for localized text results."""

    timezone: str
    """IANA time zone of the user, for parsing and formatting times."""

    threadId: NotRequired[str]
    """ID of the conversation the tool is called from. Absent for scheduled runs and MCP clients."""


class AssistantToolImage(TypedDict):
    """An image a tool returns alongside its text. Forwarded to the model only
    when the instance allows images to leave the machine, so ``content`` should
    still describe what the image shows."""

    data: str
    """Base64-encoded image bytes."""

    mimeType: Literal["image/jpeg", "image/png", "image/webp"]
    """MIME type of ``data``."""

    caption: NotRequired[str]
    """Short caption shown to the user next to the image."""


class AssistantToolReference(TypedDict):
    """Something in the app a tool result points at. The chat renders it as a
    button that opens the matching view: the recording player for an event,
    the episode player for an episode, the camera page for a camera, or a
    download button for a file the download manager serves."""

    kind: Literal["event", "episode", "camera", "download"]
    """What the id names."""

    id: str
    """Id of the event, episode or camera, or the download token."""

    label: NotRequired[str]
    """Short label for the button, for example the camera name and time."""

    cameraId: NotRequired[str]
    """Camera the event belongs to, required for ``event``."""

    timestamp: NotRequired[int]
    """Start of the event or episode in milliseconds since the epoch, required for ``event``."""

    url: NotRequired[str]
    """Download path from the download manager, required for ``download``; the chat shows a download button labelled with ``label``."""


class AssistantToolResult(TypedDict):
    """Result of a tool call. Return ``error`` for problems the model can repair
    by asking differently (unknown camera, empty range); raise only for
    failures that should end the run."""

    content: NotRequired[str | dict[str, Any] | list[Any]]
    """Text or JSON the model reads. The host serializes JSON."""

    images: NotRequired[list[AssistantToolImage]]
    """Images to show and, when allowed, to send to the model."""

    references: NotRequired[list[AssistantToolReference]]
    """Things the chat should offer to open, at most a handful per result."""

    error: NotRequired[str]
    """User-level problem the model may repair. Replaces ``content``."""


@runtime_checkable
class AssistantToolProvider(Protocol):
    """Implemented by plugins that list ``PluginInterface.AssistantTools`` in
    their contract. The host asks for the tool list once after the plugin is
    ready and dispatches calls by name.

    Example:
        ```python
        class MyPlugin(BasePlugin):
            async def assistantTools(self) -> list[AssistantToolSpec]:
                return [query_events]

            async def callAssistantTool(
                self, name: str, input: dict[str, Any], ctx: AssistantToolContext
            ) -> AssistantToolResult:
                if name == "query_events":
                    return {"content": await self.store.query(input["from"], input["to"])}
                return {"error": f"Unknown tool {name}"}
        ```
    """

    async def assistantTools(self) -> list[AssistantToolSpec]:
        """List the tools this plugin offers. Called once per plugin start.

        Returns:
            The tool specs, empty when the plugin currently has none.
        """
        ...

    async def callAssistantTool(
        self, name: str, input: dict[str, Any], ctx: AssistantToolContext
    ) -> AssistantToolResult:
        """Run one tool. Validate ``input`` against the declared schema, the
        host does not.

        Args:
            name: Tool name as declared in ``AssistantToolSpec["name"]``.
            input: Parsed arguments the model produced.
            ctx: Who is asking and in which language.

        Returns:
            Text, JSON or images for the model, or an ``error`` it may repair.
        """
        ...


def define_assistant_tool(spec: AssistantToolSpec) -> AssistantToolSpec:
    """Identity helper that types a tool spec, so a typo in a property type is
    a type-check error instead of a runtime surprise.

    Args:
        spec: The tool spec.

    Returns:
        The same spec, unchanged.

    Example:
        ```python
        set_favorite = define_assistant_tool(
            {
                "name": "set_favorite",
                "description": "Mark or unmark a recorded event as favorite.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"eventId": {"type": "string"}, "favorite": {"type": "boolean"}},
                    "required": ["eventId", "favorite"],
                },
                "approval": True,
            }
        )
        ```
    """
    return spec
