from importlib import import_module


def test_phase_one_packages_are_importable() -> None:
    package_names = (
        "app",
        "app.api",
        "app.web",
        "app.workspace",
        "app.harness",
        "app.model_runtime",
    )

    imported_names = tuple(import_module(name).__name__ for name in package_names)

    assert imported_names == package_names
