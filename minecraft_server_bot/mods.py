import json
import zipfile
from pathlib import Path
from typing import Any

import toml


class Mod:
    def __init__(self, *, name: str, version: str, loader: str):
        self.name = name
        self.version = version
        self.loader = loader

    @classmethod
    def from_fabric_data(cls, data: dict[str, Any]) -> "Mod":
        return cls(name=data["name"], version=data["version"], loader="fabric")

    @classmethod
    def from_forge_data(cls, data: dict[str, Any]) -> "Mod":
        return cls(name=data["displayName"], version=data["version"], loader="forge")

    @classmethod
    def from_jar(cls, path: Path | str) -> "Mod":
        with zipfile.ZipFile(path) as file:
            members = file.namelist()
            if "fabric.mod.json" in members:
                data = json.load(file.open("fabric.mod.json"))
                return cls.from_fabric_data(data)
            elif "META-INF/mods.toml" in members:
                for encoding in ["utf-8", "cp1252"]:
                    try:
                        file_contents = (
                            file.open("META-INF/mods.toml").read().decode(encoding)
                        )
                        data = toml.loads(file_contents)
                    except ValueError:
                        continue
                    else:
                        mods_data = data["mods"]
                        for mod_data in mods_data:
                            return cls.from_forge_data(mod_data)
