"""Serializer handles matching of selector to the proper protobuf message definition."""
import importlib
import logging
import os
import pathlib
import re
import sys
from typing import Dict, Optional, List, Any

from google.protobuf import json_format

from ostorlab import exceptions

PROTO_CLASS_NAME = 'Message'

# When the package is built, the proto files are not shipped, only the compiled version, which have the
# form: logs_pb2.cpython-38.pyc
MESSAGE_PROTO = '_pb2'
MESSAGE_CODE_PATH = pathlib.Path(__file__).parent / 'proto'

logger = logging.getLogger(__name__)

class SerializationError(exceptions.OstorlabError):
    """Base serialization Error."""


class TooManyMatchingPackageNamesError(SerializationError):
    """There are over 2 matching package names."""


class NoMatchingPackageNameError(SerializationError):
    """There are no matching package name."""


def _find_package_name(selector: str) -> Optional[str]:
    """Finds matching package name to selector."""
    files = _list_message_proto_files()
    regex_pattern = _selector_to_package_regex(selector)
    logger.debug('searching protos with pattern: %s', regex_pattern)
    pattern = re.compile(regex_pattern)
    matching = [pattern.match(f) for f in files]
    filtered_matching = [m.group(0) for m in matching if m is not None]
    if len(filtered_matching) > 1:
        raise TooManyMatchingPackageNamesError(f'Found {",".join(filtered_matching)}')
    elif len(filtered_matching) == 0:
        raise NoMatchingPackageNameError()
    else:
        return _replace_module_proto(filtered_matching[0])


def _replace_module_proto(proto_path: str) -> str :
    if sys.platform == 'win32':
        # Remove the path to the current package.
        matching_package = re.sub(r'^.*\\ostorlab', 'ostorlab', proto_path)
        # Replace \ with .
        matching_package = matching_package.replace('\\', '.')
    else:
        # Remove the path to the current package.
        matching_package = re.sub(r'^.*/ostorlab/', 'ostorlab/', proto_path)
        # Replace / with .
        matching_package = matching_package.replace('/', '.')

    # Point to the compiled protobufs.
    return re.sub(r'_pb2\..*$', '_pb2', re.sub(r'^\.code\.', '', matching_package))


def _list_message_proto_files() -> List[str]:
    """List all the proto files."""
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(MESSAGE_CODE_PATH):
        for file in f:
            if MESSAGE_PROTO in file:
                files.append(os.path.join(r, file))
        del d
    return files


def _selector_to_package_regex(subject):
    """Maps selector to package matching regular expression."""
    splitted = subject.split('.')
    if sys.platform == 'win32':
        return '.*\\\\message\\\\proto\\\\' +\
               '\\\\'.join([f'(_[_a-zA-Z0-9]+|{s})' for s in splitted]) + r'..[_a-zA-Z0-9]+\_pb2\.py'
    else:
        return '.*/message/proto/' + '/'.join([f'(_[_a-zA-Z0-9]+|{s})' for s in splitted]) + r'.[_a-zA-Z0-9]+\_pb2\.py'


def serialize(selector: str, values: Dict[str, Any]):
    """Serializes a Request message using the proper format defined using the seelctor value.
    If the subject is a.b.c. The corresponding proto is located at message/a/b/c/xxx.proto.

    Args:
        selector: Message selector, must specify the version in use.
        values: Dict representation of the message to serialize.

    Returns:
        Proto serialized message.
    """
    try:
        return _serialize(selector, PROTO_CLASS_NAME, values)
    except json_format.Error as e:
        raise SerializationError('Error serializing message') from e


def _serialize(selector: str, class_name: str, values: Dict[str, Any]):
    """Serializes message using the selector and defined class name."""
    package_name = _find_package_name(selector)
    class_object = getattr(importlib.import_module(package_name), class_name)
    proto_message = class_object()
    _parse_dict(values, proto_message)
    return proto_message


def _parse_list(values: Any, message) -> None:
    """Parse list to protobuf message."""
    if len(values) > 0 and isinstance(values[0], dict):  # value needs to be further parsed
        for v in values:
            cmd = message.add()
            _parse_dict(v, cmd)
    else:  # value can be set
        message.extend(values)


def _parse_dict(values: Any, message) -> None:
    """Parse dict to protobuf message."""
    for k, v in values.items():
        if isinstance(v, dict):  # value needs to be further parsed
            _parse_dict(v, getattr(message, k))
        elif isinstance(v, list):
            _parse_list(v, getattr(message, k))
        else:
            try:
                # if is of type ENUM.
                if message.DESCRIPTOR.fields_by_name[k].type == 14:
                    # For type enum, we introspect the type to get enum type, and then get the string mapping to int.
                    enum_v = message.DESCRIPTOR.fields_by_name[k].enum_type.values_by_name[v].number
                    setattr(message, k, enum_v)
                elif v is None:
                    # Optional values don't need to be set.
                    pass
                else:
                    setattr(message, k, v)
            except AttributeError as e:
                raise SerializationError(f'invalid attribute {k}') from e
            except KeyError as e:
                raise SerializationError(f'invalid attribute {k}') from e


def deserialize(selector: str, serialized: bytes):
    """Deserializes a Request message using the proper format defined using the selector value.

    Args:
        selector: Message selector, must specify the version in use.
        serialized: Raw message to deserialize.

    Returns:
        Dict
    """
    return _deserialize(selector, PROTO_CLASS_NAME, serialized)


def _deserialize(selector: str, class_name: str, serialized: bytes):
    """Deserializes message using the selector and defined class name."""
    package_name = _find_package_name(selector)
    class_object = getattr(importlib.import_module(package_name), class_name)
    proto_message = class_object()
    proto_message.ParseFromString(serialized)
    return proto_message
