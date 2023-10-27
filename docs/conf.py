import os
import re
import sys
from datetime import datetime

sys.path.append(os.path.abspath("../"))

from a3m.cli.common import init_django

init_django()

needs_sphinx = "3.2"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinxcontrib.mermaid",
]

autoclass_content = "both"
autodoc_member_order = "bysource"
source_suffix = ".rst"
master_doc = "index"
project = "a3m"
author = "%d Artefactual Systems Inc." % datetime.now().year

output = os.popen("git describe --tags --abbrev=0").read().strip()  # nosec
release = re.sub("^v", "", output)
version = release

language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "sphinx"
todo_include_todos = True

html_theme = "alabaster"
html_theme_options = {
    "description": "Lightweight Archivematica",
    "fixed_sidebar": True,
    "github_user": "artefactual-labs",
    "github_repo": "a3m",
    "github_banner": False,
    "github_button": False,
}
html_static_path = ["_static"]
htmlhelp_basename = "a3mdoc"

suppress_warnings = ["image.nonlocal_uri"]

mermaid_version = "8.8.2"
