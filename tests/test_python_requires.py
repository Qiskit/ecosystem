# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Tests for the qiskit requirements a repository manifest declares

`[[python.requires]]`, the counterpart of `[[pypi.requires]]`: a manifest can put its
qiskit in `[project.optional-dependencies]`, so a project that needs it for one feature
declares none outside that extra.
"""

from tests.test_python import PythonDataTestCase, conditions


class TestTheDeclaredQiskitRequirements(PythonDataTestCase):
    """What the manifest reader makes of an optional qiskit"""

    def test_a_qiskit_in_an_extra_is_declared(self):
        """`qem-auditor` puts its qiskit in an `adapters` extra, and was read as having none.

        The manifest reader looked at `[project.dependencies]` only, so a project that
        needs qiskit for one feature declared nothing at all.
        """
        data = self.fetched(
            pyproject={
                "project": {
                    "name": "banana-compiler",
                    "dependencies": ["numpy>=2"],
                    "optional-dependencies": {"adapters": ["qiskit>=2.0"]},
                }
            }
        )

        self.assertEqual(
            [{"specifier": ">=2.0", "extra": "adapters"}],
            [conditions(row) for row in data.requires],
        )

    def test_a_manifest_whose_qiskit_is_conditional_claims_none(self):
        """As `[[pypi]]`: installing the project does not bring qiskit in"""
        data = self.fetched(
            pyproject={
                "project": {
                    "name": "banana-compiler",
                    "optional-dependencies": {"adapters": ["qiskit>=2.0"]},
                }
            }
        )

        self.assertNotIn("requires_qiskit", data.to_dict())
        self.assertNotIn("compatible_with_qiskit_v2", data.to_dict())

    def test_every_extra_is_declared_including_a_docs_one(self):
        """A `docs` extra asking for qiskit is still a declaration the manifest makes.

        `qiskit-noise-learning` wants `qiskit[visualization]` so Sphinx can render a
        circuit, with no specifier at all. Which extras are worth acting on is a
        judgement for a reader of the records, and the `extra` on each entry is what
        lets one be made.
        """
        data = self.fetched(
            pyproject={
                "project": {
                    "name": "banana-compiler",
                    "dependencies": ["qiskit<3,>=2.5.0"],
                    "optional-dependencies": {
                        "docs": ["qiskit[visualization]"],
                        "adapters": ["qiskit>=2"],
                    },
                }
            }
        )

        self.assertEqual(
            [
                {"specifier": "<3,>=2.5.0"},
                {"specifier": ">=0", "extra": "docs"},
                {"specifier": ">=2", "extra": "adapters"},
            ],
            [conditions(row) for row in data.requires],
        )

    def test_setup_cfg_extras_are_read(self):
        """setup.cfg keeps each extra as an indented multi-line string"""
        data = self.fetched(
            setup_cfg={
                "metadata": {"name": "banana-compiler"},
                "options.extras_require": {"adapters": "qiskit>=2.0\nqiskit-aer>=0.14"},
            }
        )

        self.assertEqual(
            [{"specifier": ">=2.0", "extra": "adapters"}],
            [conditions(row) for row in data.requires],
        )
