"""Minimal ODS reader for tabular sheets used by the Streamlit app."""

from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import BinaryIO

import pandas as pd


NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}

TABLE_NAME = f"{{{NS['table']}}}name"
ROW_REPEAT = f"{{{NS['table']}}}number-rows-repeated"
COL_REPEAT = f"{{{NS['table']}}}number-columns-repeated"
OFFICE_VALUE = f"{{{NS['office']}}}value"


def read_ods_sheet_names(source: str | Path | BinaryIO) -> list[str]:
    root = _read_content_xml(source)
    spreadsheet = root.find(".//office:spreadsheet", NS)
    if spreadsheet is None:
        return []
    return [sheet.attrib.get(TABLE_NAME, "") for sheet in spreadsheet.findall("table:table", NS)]


def read_ods(source: str | Path | BinaryIO, sheet_name: str | None = None) -> pd.DataFrame:
    root = _read_content_xml(source)
    spreadsheet = root.find(".//office:spreadsheet", NS)
    if spreadsheet is None:
        return pd.DataFrame()

    sheets = spreadsheet.findall("table:table", NS)
    if not sheets:
        return pd.DataFrame()

    if sheet_name is None:
        sheet = sheets[0]
    else:
        matches = [item for item in sheets if item.attrib.get(TABLE_NAME) == sheet_name]
        if not matches:
            raise ValueError(f"ODS sheet not found: {sheet_name}")
        sheet = matches[0]

    rows = _sheet_rows(sheet)
    rows = [row for row in rows if any(str(value).strip() for value in row)]
    if not rows:
        return pd.DataFrame()

    headers = [str(value).strip() if str(value).strip() else f"column_{i}" for i, value in enumerate(rows[0], start=1)]
    width = len(headers)
    body = [row[:width] + [""] * max(width - len(row), 0) for row in rows[1:]]
    frame = pd.DataFrame(body, columns=headers).replace("", pd.NA)
    for column in frame.columns:
        converted = pd.to_numeric(frame[column], errors="coerce")
        if converted.notna().sum() == frame[column].notna().sum():
            frame[column] = converted
    return frame


def _read_content_xml(source: str | Path | BinaryIO) -> ET.Element:
    if hasattr(source, "seek"):
        source.seek(0)
    with zipfile.ZipFile(source) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    if hasattr(source, "seek"):
        source.seek(0)
    return root


def _sheet_rows(sheet: ET.Element) -> list[list[object]]:
    rows: list[list[object]] = []
    for row in sheet.findall("table:table-row", NS):
        row_repeat = int(row.attrib.get(ROW_REPEAT, "1"))
        values = _row_values(row)
        repeat_count = min(row_repeat, 1 if any(str(value).strip() for value in values) else 0)
        for _ in range(repeat_count):
            rows.append(values)
    return rows


def _row_values(row: ET.Element) -> list[object]:
    values: list[object] = []
    for cell in row.findall("table:table-cell", NS):
        repeat = int(cell.attrib.get(COL_REPEAT, "1"))
        value = cell.attrib.get(OFFICE_VALUE)
        if value is None:
            value = "".join(text.text or "" for text in cell.findall(".//text:p", NS))
        values.extend([value] * min(repeat, 256))
    while values and not str(values[-1]).strip():
        values.pop()
    return values
