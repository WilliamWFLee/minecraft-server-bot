import itertools
import json
import re
import zipfile
from pathlib import Path
from typing import TypeVar

import toml

ModType = TypeVar("ModType", bound="Mod")


class Mod:
    def __init__(self, *, name: str, version: str, loader: str):
        self.name = name
        self.version = version
        self.loader = loader

    @classmethod
    def from_jar(cls, path: Path | str) -> list[ModType]:
        with zipfile.ZipFile(path) as file:
            members = file.namelist()
            if "fabric.mod.json" in members:
                return FabricMod.from_jar(file)
            elif "META-INF/mods.toml" in members:
                return ForgeMod.from_jar(file)

    @classmethod
    def from_jars(cls, paths: list[Path | str]) -> list[ModType]:
        mods = list(itertools.chain.from_iterable(Mod.from_jar(path) for path in paths))
        mods = sorted(mods, key=lambda mod: mod.name)

        return mods


class FabricMod(Mod):
    @classmethod
    def from_jar(cls, zipfile: zipfile.ZipFile) -> list["FabricMod"]:
        data = json.load(zipfile.open("fabric.mod.json"))
        mod = cls(name=data["name"], version=data["version"], loader="fabric")
        if mod:
            return [mod]
        return []


class ForgeMod(Mod):
    IMPLEMENTATION_VERSION_REGEX = re.compile(
        r"Implementation-Version: (?P<version>.*)"
    )

    @classmethod
    def from_jar(cls, zipfile: zipfile.ZipFile) -> list["ForgeMod"]:
        data = cls._read_mods_toml(zipfile)
        if data is None:
            return []

        mods = []
        file_jar_version = None
        for mod_data in data["mods"]:
            version = mod_data["version"]
            if version == "${file.jarVersion}":
                if not file_jar_version:
                    file_jar_version = cls._read_implementation_version(zipfile)
                version = file_jar_version

            mod = cls(
                name=mod_data["displayName"],
                version=version,
                loader="forge",
            )
            mods.append(mod)

        return mods

    @staticmethod
    def _read_mods_toml(zipfile: zipfile.ZipFile) -> dict:
        for encoding in ["utf-8", "cp1252"]:
            try:
                file_contents = (
                    zipfile.open("META-INF/mods.toml").read().decode(encoding)
                )
            except ValueError:
                continue
            else:
                return toml.loads(file_contents)

    @classmethod
    def _read_implementation_version(cls, zipfile: zipfile.ZipFile) -> dict:
        for encoding in ["utf-8", "cp1252"]:
            try:
                file_contents = (
                    zipfile.open("META-INF/MANIFEST.MF").read().decode(encoding)
                )
            except ValueError:
                continue
            else:
                if match := cls.IMPLEMENTATION_VERSION_REGEX.search(file_contents):
                    return match.group("version")
