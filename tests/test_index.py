import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json

import pytest

from util.construct import generate_title_variants
from util.index import build_search_index, create_new_empty_index, search_matches
from util.normalization import normalize_titles


def create_mock_asset(title, asset_type="collections"):
    return {
        "title": title,
        "normalized_title": normalize_titles(title),
        "files": [f"{title}.jpg"],
        "type": asset_type,
    }

@pytest.mark.parametrize("asset_title,media_title,should_match", [
    ("Hulu (US) Shows", "Hulu Shows", True),
    ("Disney (UK) Movies", "Disney Movies", True),
    ("Apple TV+ Shows", "Apple TV Plus Shows", True),  
    ("HBO Collection", "HBO", True),
    ("Paramount (CA) Movies", "Paramount Movies", True),
    ("OZ Collection", "OZ", True),
])
def test_prefix_index_lookup(asset_title, media_title, should_match):
    index = create_new_empty_index()
    asset = create_mock_asset(asset_title)
    build_search_index(index, asset["title"], asset, logger=None)

    # Like util.match: search the media title plus its generated alternate titles
    titles_to_try = [media_title] + generate_title_variants(media_title)["alternate_titles"]
    results = [r for title in titles_to_try for r in search_matches(index, title, logger=None)]
    match_titles = [r["title"] for r in results]
    print(f"Prefix_index: {json.dumps(index, indent=2)}")
    print(f"Results: {json.dumps(results, indent=2)}")
    if should_match:
        assert asset["title"] in match_titles, f"Expected '{asset['title']}' to match '{media_title}'"
    else:
        assert asset["title"] not in match_titles, f"Did not expect '{asset['title']}' to match '{media_title}'"