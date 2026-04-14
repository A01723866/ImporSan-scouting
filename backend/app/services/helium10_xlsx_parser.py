"""
Helium 10 Xray .xlsx parser.

Helium 10 embeds product images that crash openpyxl on drawing XML.
We bypass this by reading the xlsx zip directly with stdlib only.
"""

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Any

_NS = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class Helium10XlsxParseError(ValueError):
    """Raised when the file cannot be parsed as a Helium 10 export."""


def parse_helium10_xlsx(file_bytes: bytes) -> list[dict[str, Any]]:
    """
    Parse a Helium 10 Xray .xlsx binary into a list of row dicts.

    Args:
        file_bytes: Raw bytes of the .xlsx file.

    Returns:
        List of dicts mapping column header → cell value (str | float | None).

    Raises:
        Helium10XlsxParseError: If the file structure is invalid.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as z:
            shared_xml = z.read("xl/sharedStrings.xml").decode("utf-8")
            sheet_xml = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise Helium10XlsxParseError(
            "Could not open xlsx. Make sure it is a valid Helium 10 Xray export."
        ) from exc

    try:
        stree = ET.fromstring(shared_xml)
    except ET.ParseError as exc:
        raise Helium10XlsxParseError("Malformed sharedStrings.xml.") from exc

    shared_strings: list[str] = []
    for si in stree.findall(".//ns:si", _NS):
        val = "".join(t.text or "" for t in si.findall(".//ns:t", _NS))
        shared_strings.append(val)

    try:
        wtree = ET.fromstring(sheet_xml)
    except ET.ParseError as exc:
        raise Helium10XlsxParseError("Malformed sheet1.xml.") from exc

    rows = wtree.findall(".//ns:row", _NS)
    if not rows:
        raise Helium10XlsxParseError("The xlsx sheet appears to be empty.")

    def _cell_value(cell) -> str | float | None:
        cell_type = cell.get("t", "")
        v_el = cell.find("ns:v", _NS)
        if v_el is None:
            return None
        raw = v_el.text
        if cell_type == "s":
            try:
                return shared_strings[int(raw)]
            except (IndexError, ValueError):
                return raw
        try:
            return float(raw)
        except (TypeError, ValueError):
            return raw

    headers: dict[str, str] = {}
    for cell in rows[0].findall("ns:c", _NS):
        match = re.match(r"([A-Z]+)", cell.get("r", ""))
        if match:
            headers[match.group(1)] = _cell_value(cell)

    if not headers:
        raise Helium10XlsxParseError("Could not read header row from the xlsx.")

    records: list[dict[str, Any]] = []
    for row in rows[1:]:
        rec: dict[str, Any] = {}
        for cell in row.findall("ns:c", _NS):
            match = re.match(r"([A-Z]+)", cell.get("r", ""))
            if match:
                col = match.group(1)
                header = headers.get(col, col)
                rec[header] = _cell_value(cell)
        records.append(rec)

    return records


def deduplicate_by_asin(records: list[dict]) -> list[dict]:
    """Remove duplicate rows keeping the first occurrence per ASIN."""
    seen: set[str] = set()
    unique: list[dict] = []
    for r in records:
        asin = r.get("ASIN")
        if asin and asin not in seen:
            seen.add(asin)
            unique.append(r)
        elif not asin:
            unique.append(r)
    return unique
