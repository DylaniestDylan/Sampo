from app.web.templates import TEMPLATE_DIRECTORY, templates


def test_base_template_is_available() -> None:
    template = templates.get_template("base.html")

    assert TEMPLATE_DIRECTORY.is_dir()
    assert template.name == "base.html"
