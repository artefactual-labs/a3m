"""
Format Policy Registry.

Rules serve as the central mechanisms that dictate how various file formats are
processed, each tailored for a specific format version and preservation purpose.
Each format version is an iteration of a broader format, categorized under a
general format group. The execution is carried out by commands, which are tied
to specific tools, ensuring every file is processed accurately. Commands are
adaptable, capable of being replaced and updated, and can even transform files
into different format versions as needed.

erDiagram

    Rule }o--o{ Rule : "replaces"
    Rule ||--o{ FormatVersion : "targets"
    Rule ||--o{ Command : "uses"

    FormatVersion }o--o{ FormatVersion: "replaces"
    FormatVersion ||--|| Format : "is a"

    Format ||--|| FormatGroup : "belongs to"

    Command }o--o{ Command: "replaces"
    Command }|--|| Tool : "uses"
    Command }o--o{ Command : "verifies"
    Command }o--o{ Command : "event details"
    Command ||--o{ FormatVersion : "outputs to"

Aspirationally, we would like to introduce the concept of a profile, i.e. a set
of rules and related objects offering a customzied approach to the processing of
digital files.
"""
from __future__ import annotations

import json
import uuid
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from enum import Enum
from importlib.resources import files
from typing import Any
from typing import Literal
from typing import Protocol
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import TypeVar

from django.apps import apps


# Avoid issues with circular imports.
if TYPE_CHECKING:
    from a3m.main.models import File
else:
    File = "File"


class RulePurpose(Enum):
    ACCESS = "access"
    CHARACTERIZATION = "characterization"
    CHARACTERIZE = "characterize"
    DEFAULT_ACCESS = "default_access"
    DEFAULT_CHARACTERIZATION = "default_characterization"
    DEFAULT_THUMBNAIL = "default_thumbnail"
    EXTRACT = "extract"
    POLICY_CHECK = "policy_check"
    PRESERVATION = "preservation"
    THUMBNAIL = "thumbnail"
    TRANSCRIPTION = "transcription"
    VALIDATION = "validation"

    def get_fallback(self) -> RulePurpose | None:
        if self is RulePurpose.THUMBNAIL:
            return RulePurpose.DEFAULT_THUMBNAIL
        if self is RulePurpose.CHARACTERIZATION:
            return RulePurpose.DEFAULT_CHARACTERIZATION
        if self is RulePurpose.ACCESS:
            return RulePurpose.DEFAULT_ACCESS
        return None


class CommandScriptType(Enum):
    AS_IS = "as_is"
    BASH_SCRIPT = "bashScript"
    COMMAND = "command"
    PYTHON_SCRIPT = "pythonScript"


class CommandUsage(Enum):
    CHARACTERIZATION = "characterization"
    EVENT_DETAIL = "event_detail"
    EXTRACTION = "extraction"
    NORMALIZATION = "normalization"
    TRANSCRIPTION = "transcription"
    VALIDATION = "validation"
    VERIFICATION = "verification"


class FormatGroup:
    """
    "fields": {
        "slug": "audio",
        "uuid": "c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        "description": "Audio"
    }
    """

    id: uuid.UUID
    slug: str
    description: str


class Format:
    """
    "fields": {
        "slug": "dolby-digital-audio",
        "group": "c94ce0e6-c275-4c09-b802-695a18b7bf2a",
        "uuid": "9426449b-6ead-4b90-a3f9-0e2f21f3bf8b",
        "description": "Dolby Digital Audio"
    }
    """

    id: uuid.UUID
    group: FormatGroup
    slug: str
    description: str


class FormatVersion:
    """
    "fields": {
        "replaces": null,
        "uuid": "8943dfdc-2b37-47df-b00f-76472e92e56d",
        "format": "ef618927-7376-4088-a761-182f7ab796bf",
        "lastmodified": "2013-11-15T01:18:30Z",
        "enabled": true,
        "access_format": false,
        "preservation_format": false,
        "version": "",
        "slug": "generic-gif",
        "pronom_id": "",
        "description": "Generic gif"
    }
    """

    id: uuid.UUID
    replaces: uuid.UUID | None
    format: Format
    last_modified: datetime
    enabled: bool
    access_format: bool
    preservation_format: bool
    version: str
    slug: str
    pronom_id: str
    description: str


class Tool:
    """
    "fields": {
        "slug": "inkscape-04831-r9886-jan-29-2013",
        "version": "0.48.3.1 r9886 (Jan 29 2013)",
        "enabled": false,
        "uuid": "06523365-9061-4ac7-a7f5-3e7e5f06ffac",
        "description": "inkscape"
    },
    """

    id: uuid.UUID
    slug: str
    version: str
    enabled: bool
    description: str


class Command:
    """
    "fields": {
        "replaces": null,
        "uuid": "6537147f-4dd4-4950-8aff-5578db9a485d",
        "lastmodified": "2013-11-15T01:18:36Z",
        "tool": "c5465b07-8dc7-475e-a5c9-ccb2ba2ed083",
        "enabled": false,
        "event_detail_command": null,
        "output_location": "",
        "command_usage": "characterization",
        "verification_command": null,
        "command": "This is a placeholder command only, and should not be called.",
        "script_type": "as_is",
        "output_format": "d60e5243-692e-4af7-90cd-40c53cb8dc7d",
        "description": "FITS"
    }
    """

    id: uuid.UUID
    replaces: uuid.UUID | None
    last_modified: datetime
    enabled: bool
    output_location: str
    command_usage: CommandUsage
    command: str
    script_type: CommandScriptType
    description: str
    tool: Tool
    output_format: FormatVersion | None
    verification_command: Command | None
    event_detail_command: Command | None


class Rule:
    """
    "fields": {
        "replaces": null,
        "uuid": "50ec04f1-372d-435d-a7c6-a548e7006d74",
        "format": "0ab4cd40-90e7-4d75-b294-498177b3897d",
        "lastmodified": "2013-11-15T01:18:38Z",
        "enabled": true,
        "command": "41112047-7ddf-4bf0-9156-39fe96b32d53",
        "purpose": "default_access"
    }
    """

    id: uuid.UUID
    replaces: uuid.UUID | None
    purpose: RulePurpose
    command: Command
    format: FormatVersion
    last_modified: datetime
    enabled: bool


class Backend(ABC):
    """Represents the contract of FPR backends.

    Backends must omit disabled or replaced objects.
    """

    @abstractmethod
    def get_format_version_by_id(self, id: uuid.UUID) -> FormatVersion | None:
        pass

    @abstractmethod
    def get_format_version_by_puid(self, puid: str) -> FormatVersion | None:
        pass

    @abstractmethod
    def get_rule_by_id(self, id: uuid.UUID) -> Rule | None:
        pass

    @abstractmethod
    def get_rules(
        self, format_version_id: uuid.UUID, purpose: RulePurpose
    ) -> list[Rule]:
        pass


class Replaceable(Protocol):
    id: uuid.UUID
    replaces: uuid.UUID | None


T = TypeVar("T", bound=Replaceable)


def get_replaced_objects(objects: dict[uuid.UUID, T]) -> dict[uuid.UUID, uuid.UUID]:
    return {obj.replaces: obj.id for obj in objects.values() if obj.replaces}


class DjangoDatabaseDumpItem(TypedDict):
    """Represents database items in a Django sqldump."""

    fields: dict[str, Any]
    model: Literal[
        "fpr.format",
        "fpr.formatgroup",
        "fpr.formatversion",
        "fpr.fpcommand",
        "fpr.fprule",
        "fpr.fptool",
    ]
    pk: int


DjangoDatabaseDumpList = list[DjangoDatabaseDumpItem]


class JSONBackend(Backend):
    formats: dict[uuid.UUID, Format]
    groups: dict[uuid.UUID, FormatGroup]
    versions: dict[uuid.UUID, FormatVersion]
    commands: dict[uuid.UUID, Command]
    rules: dict[uuid.UUID, Rule]
    tools: dict[uuid.UUID, Tool]

    replaced_versions: dict[uuid.UUID, uuid.UUID]
    replaced_commands: dict[uuid.UUID, uuid.UUID]
    replaced_rules: dict[uuid.UUID, uuid.UUID]

    def __init__(self, blob):
        self._load(json.loads(blob))

    def _load(self, data: DjangoDatabaseDumpList):
        self.formats = {}
        self.groups = {}
        self.versions = {}
        self.commands = {}
        self.rules = {}
        self.tools = {}

        # Load format groups.
        for item in data:
            model, fields = item["model"], item["fields"]
            id = uuid.UUID(fields["uuid"])
            if model == "fpr.formatgroup":
                group = FormatGroup()
                self.groups[id] = group
                group.id = id
                group.slug = fields["slug"]
                group.description = fields["description"]

        # Load formats.
        for item in data:
            model, fields = item["model"], item["fields"]
            id = uuid.UUID(fields["uuid"])
            if model == "fpr.format":
                format = Format()
                self.formats[id] = format
                format.id = id
                format.slug = fields["slug"]
                format.description = fields["description"]
                format.group = self.groups[uuid.UUID(fields["group"])]

        # Load format versions.
        for item in data:
            model, fields = item["model"], item["fields"]
            id = uuid.UUID(fields["uuid"])
            if model == "fpr.formatversion":
                version = FormatVersion()
                self.versions[id] = version
                version.id = id
                version.replaces = (
                    uuid.UUID(fields["replaces"]) if fields["replaces"] else None
                )
                version.last_modified = convert_django_date_to_datetime(
                    fields["lastmodified"]
                )
                version.enabled = fields["enabled"]
                version.access_format = fields["access_format"]
                version.preservation_format = fields["preservation_format"]
                version.version = fields["version"]
                version.slug = fields["slug"]
                version.pronom_id = fields["pronom_id"]
                version.description = fields["description"]
                version.format = self.formats[uuid.UUID(fields["format"])]
        self.replaced_versions = get_replaced_objects(self.versions)

        # Load tools.
        for item in data:
            model, fields = item["model"], item["fields"]
            id = uuid.UUID(fields["uuid"])
            if model == "fpr.fptool":
                tool = Tool()
                self.tools[id] = tool
                tool.id = id
                tool.slug = fields["slug"]
                tool.description = fields["description"]
                tool.version = fields["version"]

        # Load commands.
        for item in data:
            model, fields = item["model"], item["fields"]
            id = uuid.UUID(fields["uuid"])
            if model == "fpr.fpcommand":
                command = Command()
                self.commands[id] = command
                command.id = id
                command.replaces = (
                    uuid.UUID(fields["replaces"]) if fields["replaces"] else None
                )
                command.enabled = fields["enabled"]
                command.last_modified = convert_django_date_to_datetime(
                    fields["lastmodified"]
                )
                command.output_location = fields["output_location"]
                command.command = fields["command"]
                command.command_usage = CommandUsage(fields["command_usage"].casefold())
                command.script_type = CommandScriptType(fields["script_type"])
                command.description = fields["description"]
                command.tool = self.tools[uuid.UUID(fields["tool"])]
                if fields["output_format"]:
                    format_version_id = uuid.UUID(fields["output_format"])
                    command.output_format = self.versions.get(format_version_id)
        self.replaced_commands = get_replaced_objects(self.commands)
        for item in data:
            model, fields = item["model"], item["fields"]
            id = uuid.UUID(fields["uuid"])
            if model == "fpr.fpcommand":
                command = self.commands[id]
                command.verification_command = self.commands.get(
                    fields["verification_command"]
                )
                command.event_detail_command = self.commands.get(
                    fields["event_detail_command"]
                )

        # Load rules.
        for item in data:
            model, fields = item["model"], item["fields"]
            id = uuid.UUID(fields["uuid"])
            if model == "fpr.fprule":
                rule = Rule()
                rule.id = id
                rule.last_modified = convert_django_date_to_datetime(
                    fields["lastmodified"]
                )
                rule.replaces = (
                    uuid.UUID(fields["replaces"]) if fields["replaces"] else None
                )
                rule.enabled = fields["enabled"]
                rule.purpose = RulePurpose(fields["purpose"])
                try:
                    rule.format = self.versions[uuid.UUID(fields["format"])]
                    rule.command = self.commands[uuid.UUID(fields["command"])]
                except KeyError:
                    pass
                else:
                    self.rules[id] = rule
        self.replaced_rules = get_replaced_objects(self.rules)

    def get_format_version_by_id(self, id: uuid.UUID) -> FormatVersion | None:
        version = self.versions.get(id)
        if (
            version is None
            or not version.enabled
            or version.id in self.replaced_versions
        ):
            return None
        return version

    def get_format_version_by_puid(self, puid: str) -> FormatVersion | None:
        for version in self.versions.values():
            if (
                version.pronom_id == puid
                and version.enabled
                and version.id not in self.replaced_versions
            ):
                return version
        return None

    def get_rule_by_id(self, id: uuid.UUID) -> Rule | None:
        return self.rules.get(id)

    def get_rules(
        self, format_version_id: uuid.UUID, purpose: RulePurpose
    ) -> list[Rule]:
        rules: list[Rule] = []
        format_version = self.versions.get(format_version_id)
        if not format_version:
            raise ValueError(f"Format version f{format_version_id} not found.")
        for rule in self.rules.values():
            if rule.format.id == format_version_id:
                if rule.purpose == purpose:
                    if rule.enabled and rule.id not in self.replaced_rules:
                        rules.append(rule)
        return rules


def convert_django_date_to_datetime(date: str) -> datetime:
    """Convert a Django date string to a datetime object."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(date, fmt)
        except ValueError:
            continue
    raise ValueError(f"String '{date}' does not match any of the expected formats.")


def convert_to_uuid(id: uuid.UUID | str) -> uuid.UUID:
    """Ensure that a string is a UUID object."""
    if isinstance(id, str):
        return uuid.UUID(id)
    return id


class Registry:
    """FPR registry with pluggable data sources (backends).

    It omits objects not in service (disabled or replaced).

    It does not import Django models to avoid circular dependency issues.
    """

    backend: Backend

    def __init__(self, backend: Backend | None = None):
        self.backend = backend or default_backend

    def _file_model(self) -> File:
        return apps.get_model("main.File")  # type: ignore

    def get_format_version_by_id(self, id: uuid.UUID) -> FormatVersion | None:
        """Returns a format version given its identifier.

        It returns None when the object is not found or is not in service.
        """
        return self.backend.get_format_version_by_id(id)

    def get_format_version_by_puid(self, puid: str) -> FormatVersion | None:
        """Returns a format version given its PRONOM identifier.

        It returns None when the object is not found or is not in service.
        """
        return self.backend.get_format_version_by_puid(puid)

    def get_rule_by_id(self, id: uuid.UUID | str) -> Rule | None:
        """Returns a rule given its identifier.

        It returns None when the object is not found or is not in service.
        """
        return self.backend.get_rule_by_id(convert_to_uuid(id))

    def get_rules(
        self, format_version_id: uuid.UUID | str, purpose: RulePurpose
    ) -> list[Rule]:
        """Return the rules for a given format version and rule purpose.

        It omits rules not in service."""
        return self.backend.get_rules(convert_to_uuid(format_version_id), purpose)

    def get_file_rules(
        self, file: uuid.UUID | str | File, purpose: RulePurpose | str, fallback=False
    ) -> list[Rule]:
        """Return the rules for a given file and rule purpose.

        It omits rules not in service.

        TODO: refactor as method of the File mode, should also typing and circular import issues.
        """
        result: list[Rule] = []
        if isinstance(purpose, str):
            purpose = RulePurpose(purpose)
        file_obj: File
        if str(type(file).__name__) == File:
            file_obj = file  # type: ignore
        elif isinstance(file, uuid.UUID):
            file_obj = self._file_model().objects.get(pk=str(file))
        elif isinstance(file, str):
            file_obj = self._file_model().objects.get(pk=file)
        else:
            raise ValueError
        for format_version_id in file_obj.fileformatversion_set.values_list(
            "format_version_id", flat=True
        ):
            rules = self.get_rules(format_version_id, purpose)
            if len(rules):
                result.extend(rules)
            elif fallback:
                if (fallback_purpose := purpose.get_fallback()) is not None:
                    result.extend(
                        self.get_rules(format_version_id, purpose=fallback_purpose)
                    )
        return result


default_backend = JSONBackend(
    files("a3m.fpr.migrations").joinpath("initial-data.json").read_bytes()
)


FPR = Registry(default_backend)
