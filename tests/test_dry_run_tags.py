"""Dry runs must not reset (remove) the checked tags when all media is already tagged."""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules import renameinatorr, upgradinatorr
from tests.arr_fakes import CHECKED_TAG, FakeArr, SilentLogger, movie


def all_tagged():
    return [movie(1, [CHECKED_TAG]), movie(2, [CHECKED_TAG])]


# ─── Upgradinatorr ─────────────────────────────────────────────

UPGRADINATORR_SETTINGS = {
    "instance": "Movies",
    "count": 1,
    "tag_name": "checked",
    "ignore_tag": "ignore",
    "unattended": True,
}


def test_upgradinatorr_dry_run_keeps_tags():
    app = FakeArr(all_tagged())
    output = upgradinatorr.process_instance(
        "radarr", UPGRADINATORR_SETTINGS, app, SilentLogger(), SimpleNamespace(dry_run=True)
    )

    assert app.removed_tags == []
    assert app.added_tags == [] and app.searched == []
    # The simulated reset still shows what the next cycle would search
    assert [item["media_id"] for item in output["data"]] == [1]


def test_upgradinatorr_unattended_resets_tags():
    app = FakeArr(all_tagged())
    upgradinatorr.process_instance(
        "radarr", UPGRADINATORR_SETTINGS, app, SilentLogger(), SimpleNamespace(dry_run=False)
    )

    assert app.removed_tags == [([1, 2], CHECKED_TAG)]
    assert app.searched == [1]
    assert app.added_tags == [(1, CHECKED_TAG)]


# ─── Renameinatorr ─────────────────────────────────────────────

def renameinatorr_config(dry_run):
    return SimpleNamespace(
        dry_run=dry_run,
        count=0,
        tag_name="checked",
        ignore_tag="ignore",
        enable_batching=False,
        rename_folders=False,
    )


def test_renameinatorr_dry_run_keeps_tags():
    app = FakeArr(all_tagged())
    output = renameinatorr.process_instance(app, "radarr", renameinatorr_config(True), SilentLogger())

    assert app.removed_tags == []
    assert app.renamed == [] and app.added_tags == []
    assert sorted(item["title"] for item in output) == ["Movie 1", "Movie 2"]


def test_renameinatorr_resets_tags():
    app = FakeArr(all_tagged())
    renameinatorr.process_instance(app, "radarr", renameinatorr_config(False), SilentLogger())

    assert app.removed_tags == [([1, 2], CHECKED_TAG)]
    assert app.renamed == [[1, 2]]
    assert app.added_tags == [([1, 2], CHECKED_TAG)]
