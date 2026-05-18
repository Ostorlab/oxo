"""Docker builder with log progress streaming."""

import itertools
import os
import re
import subprocess
from typing import Generator, Dict, Any, Optional, Tuple

import docker
from docker.errors import BuildError
from docker.models import images
from docker.models.resource import Collection
from docker.utils.json_stream import json_stream


class BuildProgress(Collection):
    """Build log progress streamer."""

    model = images.Image

    def __init__(self) -> None:
        super().__init__(client=docker.from_env())

    def build(
        self, **kwargs: Any
    ) -> Generator[Dict[str, Any], None, Optional[Tuple[Any, Any]]]:
        """Build command that copies the initial implementation with log streaming.

        Args:
            **kwargs:

        Yields:
            Log dict with stream or aux as keys and log content in the value.
        """
        try:
            return self._build_with_cli(**kwargs)
        except (subprocess.CalledProcessError, BuildError):
            return self._build_with_sdk(**kwargs)

    def _build_with_cli(
        self, **kwargs: Any
    ) -> Generator[Dict[str, Any], None, Optional[Tuple[Any, Any]]]:
        """Build using Docker CLI to support BuildKit features."""

        path = kwargs.get("path", ".")
        dockerfile = kwargs.get("dockerfile")
        tag = kwargs.get("tag")
        labels = kwargs.get("labels", {})
        nocache = kwargs.get("nocache", False)

        command = ["docker", "build", "--progress=plain"]
        if tag:
            command.extend(["-t", tag])
        if dockerfile:
            command.extend(["-f", dockerfile])
        if nocache:
            command.append("--no-cache")
        for key, value in labels.items():
            command.extend(["--label", f"{key}={value}"])
        command.append(path)

        build_env = os.environ.copy()
        build_env["DOCKER_BUILDKIT"] = "1"

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=build_env,
        )

        image_id = None
        for line in process.stdout:
            yield {"stream": line}
            if "Successfully built" in line or "sha256:" in line:
                match = re.search(r"(Successfully built |sha256:)([0-9a-f]+)", line)
                if match:
                    image_id = match.group(2)

        process.wait()
        if process.returncode != 0:
            yield {
                "error": f"Docker build failed with return code {process.returncode}"
            }
            raise BuildError(
                f"Docker build failed with return code {process.returncode}", None
            )

        if image_id:
            return (self.get(image_id), None)
        elif tag:
            return (self.get(tag), None)

        return None

    def _build_with_sdk(
        self, **kwargs: Any
    ) -> Generator[Dict[str, Any], None, Optional[Tuple[Any, Any]]]:
        """SDK-based build."""
        resp = self.client.api.build(**kwargs)
        if isinstance(resp, str):
            return self.get(resp)
        last_event = None
        image_id = None
        result_stream, internal_stream = itertools.tee(json_stream(resp))
        for chunk in internal_stream:
            yield chunk
            if "error" in chunk:
                raise BuildError(chunk["error"], result_stream)
            if "stream" in chunk:
                match = re.search(
                    r"(^Successfully built |sha256:)([0-9a-f]+)$", chunk["stream"]
                )
                if match:
                    image_id = match.group(2)
            last_event = chunk
        if image_id:
            return (self.get(image_id), result_stream)
        raise BuildError(last_event or "Unknown", result_stream)

    def get(self, key: str) -> Any:
        """
        Gets an image.

        Args:
            key (str): The name of the image.

        Returns:
            (:py:class:`Image`): The image.

        Raises:
            :py:class:`docker.errors.ImageNotFound`
                If the image does not exist.
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        return self.prepare_model(self.client.api.inspect_image(key))
