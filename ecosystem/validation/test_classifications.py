"""Validations involving resources/classification.toml"""

# pylint: disable=missing-function-docstring, redefined-outer-name


from os import path
from pathlib import Path
import tomllib

import pytest


@pytest.fixture
def toml_file_data():
    root_path = Path(__file__).parent.parent.parent.resolve()
    labels_toml = path.abspath(Path(root_path, "resources", "classifications.toml"))
    with open(labels_toml, "rb") as f:
        data = tomllib.load(f)
    return data


@pytest.fixture
def interfaces(toml_file_data):
    return [c["name"] for c in toml_file_data["interfaces"]]


@pytest.fixture
def categories(toml_file_data):
    return [c["name"] for c in toml_file_data["category"]]


@pytest.fixture
def labels(toml_file_data):
    return [c["name"] for c in toml_file_data["labels"]]


@pytest.fixture
def pattern_steps(toml_file_data):
    return [c["name"] for c in toml_file_data["pattern_steps"]]


@pytest.fixture
def support(toml_file_data):
    return [c["name"] for c in toml_file_data["maturity"]]


def test_valid_interfaces(member, interfaces):
    """007"""
    assert (
        hasattr(member, "interfaces") and member.interfaces
    ), "the entry `member.interfaces` does not exist and it is mandatory"

    for interface in member.interfaces:
        assert (
            interface in interfaces
        ), f"the interface '{interface}' does not exist in classifications.toml"


def test_valid_category(member, categories):
    """008"""
    assert (
        member.category in categories
    ), "member.category should exist in classifications.toml"


def test_valid_label(member, labels):
    """009"""
    for label in member.labels:
        assert (
            label in labels
        ), f"the label '{label}' does not exist in classifications.toml"


def test_005(member, pattern_steps):
    """All `member.pattern_steps` should exist in https://qisk.it/ecosystem-pattern_steps"""
    if not member.pattern_steps:
        pytest.skip("No Qiskit Pattern step declared")
    for pattern_step in member.pattern_steps:
        assert (
            pattern_step in pattern_steps
        ), f"the Qiskit Pattern step '{pattern_step}' does not exist in classifications.toml"
