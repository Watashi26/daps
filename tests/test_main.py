import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
from multiprocessing import Process
from types import SimpleNamespace

import pytest

import main
from main import ModuleManager


class DummyLogger:
    def __init__(self):
        self.logs = []

    def info(self, msg): self.logs.append(f"INFO: {msg}")
    def debug(self, msg): self.logs.append(f"DEBUG: {msg}")
    def warning(self, msg): self.logs.append(f"WARNING: {msg}")
    def error(self, msg): self.logs.append(f"ERROR: {msg}")

def dummy_module():
    time.sleep(1)

def dummy_run_module(module_name, logger):
    # Like main.run_module: returns an already started process
    process = Process(target=dummy_module)
    process.start()
    return process

def dummy_check_schedule(module_name, schedule_time, logger):
    return True

def test_module_manager_run_and_cleanup():
    logger = DummyLogger()
    manager = ModuleManager(logger)
    manager.run("dummy_module", dummy_run_module)

    assert manager.is_already_running("dummy_module")
    assert manager.has_running_modules()

    time.sleep(1.5)
    manager.cleanup()

    assert not manager.is_already_running("dummy_module")
    assert not manager.has_running_modules()

def test_module_manager_run_if_due_runs_once_per_window():
    logger = DummyLogger()
    manager = ModuleManager(logger)
    started = []

    def counting_run_module(module_name, logger):
        started.append(module_name)
        return dummy_run_module(module_name, logger)

    manager.run_if_due("dummy_module", "daily(10:00)", dummy_check_schedule, counting_run_module)
    manager.run_if_due("dummy_module", "daily(10:00)", dummy_check_schedule, counting_run_module)

    assert started == ["dummy_module"]
    manager.running_modules["dummy_module"].join()

# ─── run_module: single-instance runs ──────────────────────────

class FakeConfig:
    def __init__(self, module_name):
        self.module_config = SimpleNamespace(
            module_name=module_name,
            instances_list=[
                {"instance": "Movies", "count": 1},
                {"instance": "TV", "count": 2},
            ],
        )
        self.instances_config = {"radarr": {"Movies": {}}, "sonarr": {"TV": {}}}

class FakeProcess:
    def __init__(self, target, args):
        self.target = target
        self.args = args
        self.started = False

    def start(self):
        self.started = True

@pytest.fixture
def fake_process(monkeypatch):
    monkeypatch.setattr(main, "Config", FakeConfig)
    monkeypatch.setattr(main.multiprocessing, "Process", FakeProcess)

def test_run_module_single_instance(fake_process):
    process = main.run_module("upgradinatorr", instance="TV")
    config = process.args[0]

    assert process.started
    assert config.instances_list == [{"instance": "TV", "count": 2}]
    assert config.run_instance == "TV"

def test_run_module_all_instances(fake_process):
    process = main.run_module("upgradinatorr")
    config = process.args[0]

    assert [entry["instance"] for entry in config.instances_list] == ["Movies", "TV"]
    assert not hasattr(config, "run_instance")
