"""Validations involving ecosystem/resources/labels.toml"""

# pylint: disable=missing-function-docstring, redefined-outer-name


from os import path
from pathlib import Path
import tomllib

import pytest


@pytest.fixture
def toml_file_data():
    dir_path = path.dirname(path.realpath(__file__))
    labels_toml = path.abspath(Path(dir_path, "..", "resources", "labels.toml"))
    with open(labels_toml, "rb") as f:
        data = tomllib.load(f)
    return data


@pytest.fixture
def labels(toml_file_data):
    return [c["name"] for c in toml_file_data["labels"]]


def test_valid_label(member, labels):
    for label in member.labels:
        assert label in labels, f"the label '{label}' does not exist in labels.toml"


@pytest.fixture
def categories(toml_file_data):
    return [c["name"] for c in toml_file_data["categories"]]


def test_valid_category(member, categories):
    assert member.group in categories, "member.group should exist in labels.toml"


@pytest.fixture
def interfaces(toml_file_data):
    return [c["name"] for c in toml_file_data["interfaces"]]


def test_valid_interfaces(member, interfaces):
    for interface in member.interfaces:
        assert (
            interfaces in interfaces
        ), f"the interface '{interface}' does not exist in labels.toml"
