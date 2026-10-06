import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from util.construct import (
    create_collection,
    create_movie,
    create_series,
    generate_title_variants,
)


def test_create_collection():
    result = create_collection("Hulu (US) Shows", None, "hulushows", ["poster.jpg"])
    assert result["type"] == "collections"
    assert result["normalized_title"] == "hulushows"
    assert result["files"] == ["poster.jpg"]

def test_generate_title_variants_logic():
    v = generate_title_variants("The Matrix Collection")
    assert "Matrix Collection" in v["alternate_titles"]  # prefix stripped
    assert "The Matrix" in v["alternate_titles"]  # suffix stripped
    assert "Matrix" in v["alternate_titles"]  # both stripped
    assert len(v["normalized_alternate_titles"]) == len(set(v["normalized_alternate_titles"]))