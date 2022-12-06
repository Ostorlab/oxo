"""Docker builder with log progress streaming."""
import itertools
import re
from typing import Generator, Dict

import docker
from docker.errors import BuildError
from docker.models import images
from docker.models.resource import Collection
from docker.utils.json_stream import json_stream


class BuildProgress(Collection):
    """Build log progress streamer."""

    model = images.Image

    def __init__(self):
        super().__init__(client=docker.from_env())

    def build(self, **kwargs) -> Generator[Dict, None, None]:
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

    def get(self, key):
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
