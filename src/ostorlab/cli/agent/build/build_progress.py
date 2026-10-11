"""Docker builder with log progress streaming."""

import itertools
import re
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterator
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import docker
from docker.errors import BuildError
from docker.models import images
from docker.models.resource import Collection
from docker.utils.json_stream import json_stream

if TYPE_CHECKING:
    _ImageCollection = Collection[images.Image]
else:
    _ImageCollection = Collection


class BuildProgress(_ImageCollection):
    """Build log progress streamer."""

    model = images.Image

    def __init__(self) -> None:
        super().__init__(client=docker.from_env())

    def build(
        self, **kwargs: Any
    ) -> Generator[
        dict[str, Any],
        None,
        images.Image | tuple[images.Image, Iterator[dict[str, Any]]],
    ]:
        """Build command that copies the initial implementation with log streaming.

        Args:
            **kwargs:

        Yields:
            Log dict with stream or aux as keys and log content in the value.
        """
        resp = self.client.api.build(**kwargs)
        if isinstance(resp, str):
            return self.get(resp)
        last_event = None
        image_id = None
        result_stream, internal_stream = itertools.tee(
            cast(Iterator[dict[str, Any]], json_stream(resp))
        )
        for chunk in internal_stream:
            yield chunk
            if "error" in chunk:
                raise cast(
                    Callable[[object, Iterator[dict[str, Any]]], BuildError], BuildError
                )(chunk["error"], result_stream)
            if "stream" in chunk:
                match = re.search(
                    r"(^Successfully built |sha256:)([0-9a-f]+)$", chunk["stream"]
                )
                if match:
                    image_id = match.group(2)
            last_event = chunk
        if image_id:
            return (self.get(image_id), result_stream)
        raise cast(
            Callable[[object, Iterator[dict[str, Any]]], BuildError], BuildError
        )(last_event or "Unknown", result_stream)

    def get(self, key: str) -> images.Image:
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
        return self.prepare_model(
            cast(Callable[[str], dict[str, Any]], self.client.api.inspect_image)(key)
        )
