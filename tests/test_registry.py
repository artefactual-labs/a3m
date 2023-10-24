import uuid
from importlib.resources import files

import pytest

from a3m.fpr.registry import JSONBackend
from a3m.fpr.registry import Registry
from a3m.fpr.registry import RulePurpose
from a3m.main.models import File


def create_file_with_version_id(id: str) -> File:
    f = File.objects.create(uuid=uuid.uuid4())
    f.fileformatversion_set.create(format_version_id=id)

    return f


@pytest.fixture(scope="module")
def registry():
    backend = JSONBackend(
        files("a3m.fpr.migrations").joinpath("initial-data.json").read_bytes()
    )
    return Registry(backend)


def test_registry_get_file_rules(db, registry):
    """Confirm that it accepts uuid.UUID, str and File."""
    file_obj = create_file_with_version_id(
        "082f3282-8331-4da4-b452-632b17e90d66"
    )  # fmt/3
    assert len(registry.get_file_rules(file_obj.uuid, RulePurpose.THUMBNAIL)) == 1
    assert len(registry.get_file_rules(str(file_obj.uuid), RulePurpose.THUMBNAIL)) == 1
    assert len(registry.get_file_rules(file_obj, RulePurpose.THUMBNAIL)) == 1


def test_registry_integrity(registry):
    """Validates the integrity of the registry.

    It depends on implementation details of the JSONBackend.
    """
    backend: JSONBackend = registry.backend

    # Verify that all replaced rules are marked as disabled.
    for rule in backend.rules.values():
        is_replaced = rule.id in backend.replaced_rules
        is_enabled = rule.enabled
        assert not (
            is_enabled and is_replaced
        ), f"Rule {rule.id} is enabled but has been replaced by Rule {backend.replaced_rules[rule.id]}."

    # Verify that all replaced versions are marked as disabled.
    for version in backend.versions.values():
        is_replaced = version.id in backend.replaced_versions
        is_enabled = version.enabled
        assert not (
            is_enabled and is_replaced
        ), f"FormatVersion {version.id} is enabled but has been replaced by FormatVersion {backend.replaced_versions[version.id]}."

    # Verify that all replaced commands are marked as disabled.
    for command in backend.commands.values():
        is_replaced = command.id in backend.replaced_versions
        is_enabled = command.enabled
        assert not (
            is_enabled and is_replaced
        ), f"Command {command.id} is enabled but has been replaced by Command {backend.replaced_versions[command.id]}."

    # Verify that rules in service depend on commands and versions in service.
    for rule in backend.rules.values():
        is_replaced = rule.id in backend.replaced_rules
        is_enabled = rule.enabled
        if is_enabled and not is_replaced:
            assert (
                rule.command.enabled
                and rule.command.id not in backend.replaced_commands
            ), f"Rule in service {rule.id} is using a Command not in service: {rule.command} ({rule.command.tool.description})."
            assert (
                rule.format.enabled and rule.format.id not in backend.replaced_versions
            ), f"Rule in service {rule.id} is using a FormatVersion not in service: {rule.format} ({rule.format.description})."
