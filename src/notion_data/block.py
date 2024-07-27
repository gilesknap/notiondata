"""
Represent the block data structure in the Notion API.

https://developers.notion.com/reference/block
"""

# TODO see here for some good tricks on how to do partial models for patching
# etc. This would avoid all the | None stuff
# https://github.com/pydantic/pydantic/issues/6381

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, TypeAlias, Union

from pydantic import (
    Field,
    TypeAdapter,
    field_serializer,
    model_validator,
)

from .enums import Color, Language
from .file import _FileUnion
from .identify import NotionUser
from .parent import _ParentUnion
from .regex import UUIDv4
from .rich_text import RichText, Url
from .root import Root, format_datetime


class _BlockCommon(Root):
    """A block in Notion"""

    object: Literal["block"] | None = None
    id: str | None = Field(
        default=None, description="The ID of the block", pattern=UUIDv4
    )
    parent: _ParentUnion | None = None
    created_time: datetime | None = None
    last_edited_time: datetime | None = None

    created_by: NotionUser | None = None
    last_edited_by: NotionUser | None = None
    has_children: bool = False
    archived: bool = False
    in_trash: bool = False
    request_id: str | None = Field(
        default=None, description="The ID of the block", pattern=UUIDv4
    )

    @field_serializer("last_edited_time", "created_time")
    def validate_time(self, time: datetime, _info):
        return format_datetime(time)

    @model_validator(mode="before")
    # for child blocks, type is not required so insert it
    # so that the discriminator is present
    def insert_type(cls, values):
        if "type" not in values:
            # type literal matches the first and only key in the dict
            values["type"] = list(values)[0]
        return values


class Bookmark(_BlockCommon):
    class _BookmarkData(Root):
        url: str
        caption: RichText

    type: Literal["bookmark"]
    bookmark: _BookmarkData


class BreadCrumb(_BlockCommon):
    type: Literal["breadcrumb"]
    breadcrumb: dict = {}


class BulletedListItem(_BlockCommon):
    class _BulletedData(Root):
        rich_text: RichText
        color: Color = Color.DEFAULT
        children: list[_ChildBlockUnion] | None = None

    type: Literal["bulleted_list_item"]
    bulleted_list_item: RichText


class Callout(_BlockCommon):
    class _CalloutData(Root):
        rich_text: RichText
        icon: str | None = None
        color: Color = Color.DEFAULT

    type: Literal["callout"]
    callout: _CalloutData


class ChildDatabase(_BlockCommon):
    class _ChildDatabaseData(Root):
        title: str

    type: Literal["child_database"]
    child_database: _ChildDatabaseData


class ChildPage(_BlockCommon):
    class _ChildPageData(Root):
        title: str

    type: Literal["child_page"]
    child_page: _ChildPageData


class Code(_BlockCommon):
    class _CodeData(Root):
        caption: RichText
        rich_text: RichText
        language: Language

    type: Literal["code"]
    code: _CodeData


class ColumnList(_BlockCommon):
    type: Literal["column_list"]
    column_list: dict = {}


class Column(_BlockCommon):
    type: Literal["column"]
    column: dict = {}


class _HeadingData(Root):
    rich_text: RichText
    color: Color = Color.DEFAULT
    is_toggleable: bool = False


class Heading1(_BlockCommon):
    type: Literal["heading_1"]
    heading_1: _HeadingData


class Divider(_BlockCommon):
    type: Literal["divider"]
    divider: dict = {}


class Embed(_BlockCommon):
    type: Literal["embed"]
    embed: Url


class Equation(_BlockCommon):
    class _EquationData(Root):
        expression: str

    type: Literal["equation"]
    equation: _EquationData


class File(_BlockCommon):
    type: Literal["file"]
    file: _FileUnion


class Heading2(_BlockCommon):
    type: Literal["heading_2"]
    heading_2: _HeadingData


class Heading3(_BlockCommon):
    type: Literal["heading_3"]
    heading_3: _HeadingData


class Image(_BlockCommon):
    class _ImageData(Root):
        file: _FileUnion

    type: Literal["image"]
    image: _ImageData


class LinkPreview(_BlockCommon):
    """
    Cannot be created by the API, only returned in the context of a page.
    """

    type: Literal["link_preview"]
    link_to: Url


class NumberedListItem(_BlockCommon):
    class _NumberedListItemData(Root):
        rich_text: RichText
        color: Color = Color.DEFAULT
        children: list[_ChildBlockUnion] | None = None

    type: Literal["numbered_list_item"]
    numbered_list_item: _NumberedListItemData


class Paragraph(_BlockCommon):
    class _ParagraphData(Root):
        rich_text: RichText
        color: Color = Color.DEFAULT
        children: list[_ChildBlockUnion] | None = None

    type: Literal["paragraph"]
    paragraph: _ParagraphData


class Quote(_BlockCommon):
    class _QuoteData(Root):
        rich_text: RichText
        color: Color = Color.DEFAULT
        children: list[_ChildBlockUnion] | None = None

    type: Literal["quote"]
    quote: _QuoteData


class SyncedBlock(_BlockCommon):
    class _SyncedBlockData(Root):
        class _SyncedFrom(Root):
            block_id: str = Field(description="The ID of the block", pattern=UUIDv4)

        synced_from: _SyncedFrom | None
        children: list[_ChildBlockUnion] | None = None

    type: Literal["synced_block"]
    synced_block: _SyncedBlockData


class Table(_BlockCommon):
    class _TableData(Root):
        table_width: int
        has_column_header: bool
        has_row_header: bool

    type: Literal["table"]
    table: _TableData


class TableRow(_BlockCommon):
    class _TableRowData(Root):
        cells: list[RichText]

    type: Literal["table_row"]
    table_row: _TableRowData


class Todo(_BlockCommon):
    class TodoData(Root):
        rich_text: RichText
        checked: bool = False
        color: Color = Color.DEFAULT
        children: list[_ChildBlockUnion] | None = None

    type: Literal["to_do"]
    to_do: TodoData


class Toggle(_BlockCommon):
    class _ToggleData(Root):
        rich_text: RichText
        color: Color = Color.DEFAULT
        children: list[_ChildBlockUnion] | None = None

    type: Literal["toggle"]
    toggle: _ToggleData


class Video(_BlockCommon):
    class _VideoData(Root):
        file: _FileUnion

    type: Literal["video"]
    video: _VideoData


""" Block is union of all block types, discriminated by type literal """
_BlockUnion: TypeAlias = Annotated[  # type: ignore
    Union[tuple(_BlockCommon.__subclasses__())],  # type: ignore
    Field(discriminator="type", description="union of block types"),
]

""" ChildBlocks do not have type so can't use it as a discriminator.
    In the model validator for these we insert the type so that
    Pytdantic can resolve the subclass of the Union - just not as easilty as
    with the discriminator.

    (unfortunately discriminators are applied before the model validator
    so we can't use type here even though the validator is adding it)
"""
_ChildBlockUnion: TypeAlias = Annotated[  # type: ignore
    Union[tuple(_BlockCommon.__subclasses__())],  # type: ignore
    Field(description="union of block types"),
]

Block = TypeAdapter(_BlockUnion)
