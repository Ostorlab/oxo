"""Proto to dict transformer.
The transformer maintains bytes format and doesn't go through intermediary JSON representation that is
both inefficient and resource intensive.

This code is credited to protobuf-to-dict. The app is written and maintained by Ben Hodgson, with significant
contributions from Nino Walker, Jonathan Klaassen, and Tristram Gräbener.
 """
from google.protobuf.descriptor import FieldDescriptor
from ostorlab import exceptions
from typing import Dict, Callable


class UnrecognisedTypeError(exceptions.OstorlabError):
    """Field type is not recognised error."""


TYPE_CALLABLE_MAP = {
    FieldDescriptor.TYPE_DOUBLE: float,
    FieldDescriptor.TYPE_FLOAT: float,
    FieldDescriptor.TYPE_INT32: int,
    FieldDescriptor.TYPE_INT64: int,
    FieldDescriptor.TYPE_UINT32: int,
    FieldDescriptor.TYPE_UINT64: int,
    FieldDescriptor.TYPE_SINT32: int,
    FieldDescriptor.TYPE_SINT64: int,
    FieldDescriptor.TYPE_FIXED32: int,
    FieldDescriptor.TYPE_FIXED64: int,
    FieldDescriptor.TYPE_SFIXED32: int,
    FieldDescriptor.TYPE_SFIXED64: int,
    FieldDescriptor.TYPE_BOOL: bool,
    FieldDescriptor.TYPE_STRING: str,
    FieldDescriptor.TYPE_BYTES: bytes,
    FieldDescriptor.TYPE_ENUM: int,
}

EXTENSION_CONTAINER = '___X'


def _repeated(type_callable) -> Callable:
    """Function handler of repeated fields."""
    return lambda value_list: [type_callable(value) for value in value_list]


def _enum_label_name(field, value) -> Callable:
    """Function handler of enum fields. Generates name instead of int."""
    return field.enum_type.values_by_number[int(value)].name


def _get_field_value_adaptor(pb, field, use_enum_labels=False) -> Callable:
    """Matches proto message or field to the proper handler."""
    if field.type == FieldDescriptor.TYPE_MESSAGE:
        # recursively encode protobuf sub-message
        return lambda pb: protobuf_to_dict(pb, use_enum_labels=use_enum_labels)

    if use_enum_labels and field.type == FieldDescriptor.TYPE_ENUM:
        return lambda value: _enum_label_name(field, value)

    if field.type in TYPE_CALLABLE_MAP:
        return TYPE_CALLABLE_MAP[field.type]

    raise UnrecognisedTypeError(f'Field {pb.__class__.__name__}.{field.name} has unrecognised type id {field.type}')


def protobuf_to_dict(pb, use_enum_labels: bool = False) -> Dict:
    """Transforms Protobuf message to dict.

    The Method maintains bytes format and do not use intermediary representation like JSON.

    Args:
        pb: Protobuf message
        use_enum_labels: Use enum string label or return enum int.

    Returns:
        Dict representation of the protbuf.
    """
    result_dict = {}
    extensions = {}
    for field, value in pb.ListFields():
        type_callable = _get_field_value_adaptor(pb, field, use_enum_labels)
        if field.label == FieldDescriptor.LABEL_REPEATED:
            type_callable = _repeated(type_callable)

        if field.is_extension:
            extensions[str(field.number)] = type_callable(value)
            continue

        result_dict[field.name] = type_callable(value)

    if extensions:
        result_dict[EXTENSION_CONTAINER] = extensions
    return result_dict
