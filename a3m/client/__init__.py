import os
import pathlib


THIS_DIR = os.path.dirname(__file__)

ASSETS_DIR = os.path.join(THIS_DIR, "assets", "")

# Use local XML schemas for validation.
os.environ["XML_CATALOG_FILES"] = str(
    pathlib.Path(__file__).parent / "assets/catalog/catalog.xml"
)
