"""Upgradinatorr's use tag limits processing to media carrying that tag."""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules import upgradinatorr
from tests.arr_fakes import CHECKED_TAG, IGNORE_TAG, USE_TAG, FakeArr, SilentLogger, movie


def settings(**overrides):
    base = {
        "instance": "Movies",
        "count": 5,
        "tag_name": "checked",
        "ignore_tag": "ignore",
        "use_tag": "4k",
        "unattended": True,
    }
    base.update(overrides)
    return base


def run(app, dry_run=False, **overrides):
    return upgradinatorr.process_instance(
        "radarr", settings(**overrides), app, SilentLogger(), SimpleNamespace(dry_run=dry_run)
    )


def test_only_media_with_use_tag_is_searched():
    app = FakeArr([movie(1, [USE_TAG]), movie(2, []), movie(3, [USE_TAG, IGNORE_TAG])])
    output = run(app)

    assert app.searched == [1]
    assert [item["media_id"] for item in output["data"]] == [1]
    assert output["total_count"] == 2  # summary counts only media with the use tag


def test_use_tag_is_case_insensitive():
    app = FakeArr([movie(1, [USE_TAG]), movie(2, [])])
    run(app, use_tag="4K")

    assert app.searched == [1]


def test_unattended_reset_only_touches_media_with_use_tag():
    app = FakeArr([movie(1, [USE_TAG, CHECKED_TAG]), movie(2, [CHECKED_TAG])])
    run(app, count=1)

    assert app.removed_tags == [([1], CHECKED_TAG)]
    assert app.searched == [1]


def test_missing_use_tag_skips_instance():
    app = FakeArr([movie(1, []), movie(2, [])])
    assert run(app, use_tag="does-not-exist") is None
    assert app.searched == [] and app.removed_tags == []


def test_use_tag_equal_to_tag_name_skips_instance():
    app = FakeArr([movie(1, [CHECKED_TAG])])
    assert run(app, use_tag="Checked") is None
    assert app.removed_tags == []


def test_empty_use_tag_processes_everything():
    app = FakeArr([movie(1, []), movie(2, [])])
    run(app, use_tag="")

    assert app.searched == [1, 2]
