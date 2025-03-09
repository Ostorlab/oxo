"""Android store package target asset."""

import dataclasses

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.store.android_store")
class AndroidStore(asset.Asset):
    """Android store package target asset."""

    package_name: str

    def __str__(self) -> str:
        return f"Android Store: ({self.package_name})"

    @classmethod
    def from_dict(cls, data: dict[str, str | bytes]) -> "AndroidStore":
        """Constructs an AndroidStore asset from a dictionary."""
        package_name = data.get("package_name", "")
        if type(package_name) is bytes:
            package_name = package_name.decode()
        if package_name == "":
            raise ValueError("package_name is missing.")
        return AndroidStore(package_name)  # type: ignore

    @property
    def proto_field(self) -> str:
        return "android_store"
