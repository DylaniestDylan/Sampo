from pathlib import Path

from fastapi.templating import Jinja2Templates


TEMPLATE_DIRECTORY = Path(__file__).parent / "templates"
STATIC_DIRECTORY = Path(__file__).parent / "static"
templates = Jinja2Templates(directory=TEMPLATE_DIRECTORY)
