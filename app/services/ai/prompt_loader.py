"""Locating, caching and rendering versioned prompt templates.

Templates are data files, not Python strings, so a prompt change is reviewable as
a diff of the text itself. The version lives in the filename, which is what makes
``questions.prompt_version`` readable in psql and in a log line — a content hash
would churn on a typo fix and tell nobody anything.

Changing a prompt's meaning means adding ``<name>.v2.md`` and bumping the ref
below. The old file stays, because rows still point at it.
"""

from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from string import Template

#: Package holding the ``prompts`` data directory.
_PACKAGE = "app.services.ai"
_DIRECTORY = "prompts"


@dataclass(frozen=True, slots=True)
class PromptRef:
    """A prompt template, identified by name and version."""

    name: str
    version: str

    @property
    def filename(self) -> str:
        """File this ref resolves to, e.g. ``question_generation.v1.md``."""
        return f"{self.name}.{self.version}.md"


QUESTION_GENERATION = PromptRef(name="question_generation", version="v1")


@lru_cache
def load_prompt(ref: PromptRef) -> str:
    """Read a template, once per process.

    ``importlib.resources`` is used rather than ``__file__`` arithmetic so that
    loading does not depend on where the package physically sits.
    """
    return files(_PACKAGE).joinpath(_DIRECTORY, ref.filename).read_text(encoding="utf-8")


def render_prompt(ref: PromptRef, **values: object) -> str:
    """Fill a template's ``$placeholders``.

    ``string.Template`` rather than ``str.format`` because these templates
    contain a JSON example, and every brace in it would otherwise have to be
    doubled.
    """
    return Template(load_prompt(ref)).substitute({key: str(value) for key, value in values.items()})
