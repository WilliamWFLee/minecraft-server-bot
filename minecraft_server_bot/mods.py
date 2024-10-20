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
        return cls(
            name=data["mods"]["displayName"],
            version=data["mods"]["version"],
            loader="forge",
        )

    @classmethod
    def from_jar(cls, path: Path | str) -> "Mod":
        with zipfile.ZipFile(path) as file:
            members = file.namelist()
            if "fabric.mod.json" in members:
                data = json.load(file.open("fabric.mod.json"))
                return cls.from_fabric_data(data)
            elif "META-INF/mods.toml" in members:
                data = toml.loads(file.open("META-INF/mods.toml").read().decode())
                return cls.from_forge_data(data)
