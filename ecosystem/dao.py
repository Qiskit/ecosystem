# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


"""
DAO for json db.

File structure:

    root_path
    └── members
        └── repo-name.toml
"""

from pathlib import Path
import shutil
import toml
from toml import TomlEncoder as TomlEncoderUpstream

from ecosystem.error_handling import logger, EcosystemError
from ecosystem.member import Member


class TomlEncoder(TomlEncoderUpstream):
    """TOML encoder that keeps short lists on a single line.

    Upstream's encoder always dumps lists multiline, which makes the diffs of
    the member TOML files noisy. This subclass renders lists inline when they
    are short enough to stay readable, and falls back to one element per line
    otherwise.
    """

    def dump_sections(self, o, sup):
        """Override to put a blank line before an array of tables.

        Upstream appends the `[[section]]` blocks straight after the scalars of the
        enclosing table, with no blank line, although it does separate the entries from
        each other. Every other table in a member file is preceded by one, so without
        this the first `[[requirements]]` butts against `status = "..."`.
        """
        retstr, retdict = super().dump_sections(o, sup)
        scalars, found, tables = retstr.partition("\n[[")
        if found and not scalars.endswith("\n"):
            # the scalars end in a newline of their own, so this is the blank line
            retstr = f"{scalars}\n\n[[{tables}"
        return retstr, retdict

    def dump_list(self, v):
        """Override to dump empty lists without trailing comma"""
        oneline = f"[{', '.join( str(self.dump_value(u)) for u in v )}]"
        multiline = (
            f"[\n{'\n'.join( '  ' + str(self.dump_value(u)) + ',' for u in v )}\n]"
        )
        if len(oneline) < 60:
            return oneline
        if len(oneline) > 65:
            max_element = max(len(str(self.dump_value(u))) for u in v if u is not None)
            if max_element <= 10:
                return oneline
            return multiline
        return oneline


#: The order the tables of a member file are written in: what the submission said, then the
#: repository and its badge, then what each registry and manifest says, then the check ups.
#: `toml` would put every `[[array]]` above every `[table]` instead, which reads backwards
#: and would reshuffle every file on the next write.
SECTION_ORDER = (
    "github",
    "badge",
    "pypi",
    "crates",
    "julia",
    "cargo",
    "python",
    "requirements",
    "checks",
)


def dumps(member_dict):
    """A member as TOML text, with its tables in the order the dict has them.

    `toml` collects the arrays of tables into a string of their own and hands the plain
    sub-tables back to the caller, so whatever the dict says the output is always scalars,
    then every `[[array]]`, then every `[table]`. That puts `[[pypi]]` above `[github]`,
    which is not where a reader of a member file looks for it, and it would reshuffle every
    file the next time an updater writes one.

    So the blocks are put back in the order of the keys of `Member.to_dict`: the submission's
    own values, then `[github]` and `[badge]`, then the package sections, then `[checks.*]`.
    """
    text = toml.dumps(member_dict, encoder=TomlEncoder(preserve=True))
    blocks, current = [], []
    for line in text.splitlines(keepends=True):
        if line.startswith("[") and current:
            blocks.append(current)
            current = []
        current.append(line)
    blocks.append(current)

    def position(block):
        """Where the section this block belongs to goes in a member file"""
        header = block[0]
        if not header.startswith("["):
            return -1  # the scalars of the submission, which stay at the top
        section = header.strip().strip("[]").split(".", 1)[0].strip('"')
        if section not in SECTION_ORDER:
            # an unknown section lands with the packaging ones rather than past `[checks]`
            return SECTION_ORDER.index("requirements")
        return SECTION_ORDER.index(section)

    arranged = sorted(
        range(len(blocks)), key=lambda index: (position(blocks[index]), index)
    )
    return "".join("".join(blocks[index]) for index in arranged)


class TomlStorage:
    """Read / write TOML files from a dict where keys are repo URLs, and values are Member objects.

    Can use as a context manager like so:

    with TomlStorage() as data:  # Data is read from TOML files
        data[name_id] = new_repo # Mutate the data
                                 # Changes are saved on exit
    """

    def __init__(self, root_path: str):
        self.toml_dir = Path(root_path, "members")
        self._data = None  # for use with context manager
        self.name_id = None  # for use with context manager (to write only one file)

    def __call__(self, name_id: str = None):
        self.name_id = name_id
        return self

    def _name_id_to_path(self, name_id):
        return self.toml_dir / f"{name_id}.toml"

    def read(self, short_id: str = None) -> dict:
        """
        Search for TOML files and read into dict with types:
        { url (str): repo (Submission) }
        """
        data = {}
        toml_patter = "*.toml"
        if short_id:
            toml_patter = (
                f"*_{short_id}.toml" if len(short_id) == 8 else f"*{short_id}.toml"
            )
        for path in self.toml_dir.glob(toml_patter):
            try:
                repo = Member.from_dict(toml.load(path))
                repo._filename = path.stem  # pylint: disable=protected-access
            except TypeError as exc:
                raise EcosystemError(f"TOML empty? {path}") from exc
            except toml.decoder.TomlDecodeError as err:
                raise EcosystemError(f"{path} unparsable TOML. {err.args[0]}") from err
            data[path.stem] = repo
        return data

    def refresh_files(self):
        """Forces dumping the DAO to files"""
        # Erase existing TOML files
        # (we erase everything to clean up any deleted repos from data)
        if self.toml_dir.exists():
            shutil.rmtree(self.toml_dir)
        self.write(self._data)

    def write(self, data: dict):
        """
        Dump everything to TOML files from dict of types
        { key (any): repo (Submission) }
        """
        if not self.toml_dir.exists():
            self.toml_dir.mkdir()

        # Write to human-readable TOML
        members = [data[self.name_id]] if self.name_id else list(data.values())
        for submission in members:
            with open(self._name_id_to_path(submission.name_id), "w") as file:
                file.write(dumps(submission.to_dict()))

    def __enter__(self) -> dict:
        if self._data is None:
            self._data = self.read()
        return self._data

    def __exit__(self, _type, _value, exception):
        if _type is not None:
            return False
        self.write(self._data)
        self.name_id = None
        return True


class DAO:
    """
    Data access object for repository database.
    """

    def __init__(self, path: str):
        """
        Args:
            path: path to store database in
        """
        self.storage = TomlStorage(path)

    def write(self, repo: Member):
        """
        Update or insert repo (identified by ID).
        """
        with self.storage(repo.name_id) as data:
            data[repo.name_id] = repo

    def delete(self, name_id: str = None):
        """Deletes repository from database.

        Args:
            name_id: ID of the project. Typically, the name of the TOML file
        """
        with self.storage() as data:
            del data[name_id]

    def get_by_url(self, url: str) -> Member:
        """
        Returns project by URL. None if the repo is not found
        """
        for project in self.get_all():
            if project.url == url:
                return project
        return None

    def __getitem__(self, name_id):
        """gets a project by name in the most inefficient way"""
        for project in self.get_all():
            if project.name_id == name_id:
                return project
        raise KeyError(f"No project with name : {name_id}")

    def get_all(self, short_id: str | None = None, sort_key=None) -> list[Member]:
        """
        Returns list of all repositories.
        """
        projects = self.storage().read(str(short_id) if short_id else None).values()
        if sort_key:
            return sorted(projects, key=sort_key)
        return projects

    def update(self, name_id: str = None, **kwargs):
        """
        Update attributes of repository.

        Args:
            name_id (str): ID of the project. Typically, name of the TOML file.
            kwargs: Names of attributes and new values. If `member` in kargs,
            the value of the argument is used to update the full project first.

        Example usage:
            update("aer_474599a", github=github_data_instance)  # updates github section
            update("aer_474599a", member=member_instance)       # updates the full member
        """
        with self.storage(name_id) as data:
            if "member" in kwargs:
                data[name_id] = kwargs["member"]
                del kwargs["member"]
            for arg, value in kwargs.items():
                current_value = data[name_id].__dict__.get(arg)
                DAO.log_update(current_value, value, arg, name_id)
                data[name_id].__dict__[arg] = value

    def refresh_files(self):
        """Forces dumping the DAO to files"""
        self.storage().refresh_files()

    def upsert_project(self, project: Member):
        """Giving a Member, updates it if exists or inserts it.
        The key to check existance is get_by_url(p["url"])"""
        if existing_member := self.get_by_url(project.url):
            self.update(existing_member.name_id, member=project)
        else:
            logger.info("New project %s (%s) ", project.name_id, project.name)
            self.write(project)

    @classmethod
    def log_update(cls, current_value, new_value, arg, project):
        """Logs the update in the DAO"""
        if isinstance(new_value, dict) and isinstance(current_value, dict):
            for key, n_value in new_value.items():
                c_value = current_value.get(key, "")
                if c_value != n_value:
                    DAO.log_update(c_value, n_value, f"{arg}.{key}", project)
        elif hasattr(new_value, "to_dict") and hasattr(current_value, "to_dict"):
            DAO.log_update(current_value.to_dict(), new_value.to_dict(), arg, project)
        else:
            if current_value != new_value:
                logger.info(
                    "Updating %s: %s (%s -> %s)",
                    project,
                    arg,
                    current_value,
                    str(new_value),
                )
