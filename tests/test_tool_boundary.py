import pytest

from app.harness import (
    HarnessToolBoundary,
    ToolRegistry,
    UnexpectedModelToolRequestError,
)


FORBIDDEN_CAPABILITY_IDENTIFIERS = (
    ("filesystem", ("filesystem", "file_system", "file.read", "path")),
    ("shell/process", ("shell", "process", "command", "terminal")),
    ("code execution", ("execute_code", "code_execution", "interpreter", "eval")),
    ("Git/VCS", ("git", "vcs", "version_control")),
    ("package management", ("package_install", "package_management", "pip")),
    ("network/browser", ("network", "http", "browser", "fetch", "url")),
    ("dynamic plugins/tools", ("plugin", "dynamic_tool", "tool_loader", "discover")),
    ("IDE/Godot", ("ide", "rider", "godot", "engine_control")),
)


def test_phase_one_tool_registry_has_no_registered_descriptions() -> None:
    registry = ToolRegistry()

    assert registry.model_tool_descriptions() == ()


def test_harness_tool_boundary_receives_registry_descriptions() -> None:
    registry = ToolRegistry()
    boundary = HarnessToolBoundary(registry=registry)

    assert boundary.model_tool_descriptions() == registry.model_tool_descriptions()
    assert boundary.model_tool_descriptions() == ()


def test_unexpected_model_tool_request_fails_closed() -> None:
    boundary = HarnessToolBoundary(registry=ToolRegistry())

    with pytest.raises(UnexpectedModelToolRequestError) as raised:
        boundary.reject_model_tool_request("filesystem.read")

    assert raised.value.code == "unsupported_model_tool_request"
    assert str(raised.value) == "model tool requests are unsupported"


def test_phase_one_model_facing_tool_surface_is_structurally_empty() -> None:
    registry = ToolRegistry()
    boundary = HarnessToolBoundary(registry=registry)

    registered_descriptions = registry.model_tool_descriptions()
    exposed_descriptions = boundary.model_tool_descriptions()

    assert isinstance(registered_descriptions, tuple)
    assert registered_descriptions == ()
    assert exposed_descriptions == registered_descriptions


@pytest.mark.parametrize(("family", "identifiers"), FORBIDDEN_CAPABILITY_IDENTIFIERS)
def test_forbidden_capability_family_is_not_registered(
    family: str,
    identifiers: tuple[str, ...],
) -> None:
    descriptions = ToolRegistry().model_tool_descriptions()
    registered_identifiers = tuple(
        (
            f"{type(description).__module__}.{type(description).__qualname__}:"
            f"{description.name}"
        ).casefold()
        for description in descriptions
    )

    assert all(
        identifier not in registered_identifier
        for identifier in identifiers
        for registered_identifier in registered_identifiers
    ), family


def test_tool_boundary_exposes_no_generic_registration_or_invocation_api() -> None:
    registry_public_methods = {
        name
        for name, value in vars(ToolRegistry).items()
        if not name.startswith("_") and callable(value)
    }
    boundary_public_methods = {
        name
        for name, value in vars(HarnessToolBoundary).items()
        if not name.startswith("_") and callable(value)
    }

    assert registry_public_methods == {"model_tool_descriptions"}
    assert boundary_public_methods == {
        "model_tool_descriptions",
        "reject_model_tool_request",
    }
