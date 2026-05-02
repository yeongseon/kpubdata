from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import sys
import traceback
from collections.abc import Iterable, Mapping, Sequence
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import cast

from kpubdata import __version__
from kpubdata.client import Client
from kpubdata.core.capability import Operation, QuerySupport
from kpubdata.core.models import DatasetRef, RecordBatch
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    ProviderResponseError,
    TransportError,
)

logger = logging.getLogger("kpubdata.cli")

_MAX_TABLE_COLUMNS = 20
_MAX_CELL_WIDTH = 40


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    parsed_values = vars(args)
    debug_enabled = _configure_logging(cast(str, parsed_values.get("log_level", "warning")))

    try:
        return _run_command(args)
    except (DatasetNotFoundError, InvalidRequestError) as exc:
        _print_error(exc)
        if debug_enabled:
            traceback.print_exc(file=sys.stderr)
        return 2
    except AuthError as exc:
        _print_error(exc)
        if debug_enabled:
            traceback.print_exc(file=sys.stderr)
        return 3
    except (TransportError, ProviderResponseError) as exc:
        _print_error(exc)
        if debug_enabled:
            traceback.print_exc(file=sys.stderr)
        return 4
    except Exception as exc:
        _print_error(exc)
        if debug_enabled:
            traceback.print_exc(file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kpubdata")
    _ = parser.add_argument("--cache", action="store_true", help="Enable response cache")
    _ = parser.add_argument(
        "--log-level",
        choices=("warning", "info", "debug"),
        default="warning",
        help="Set the kpubdata logger level",
    )
    _ = parser.add_argument(
        "--provider-key",
        action="append",
        default=[],
        metavar="PROVIDER=KEY",
        help="Override a provider API key",
    )
    _ = parser.add_argument("--version", action="store_true", help="Print kpubdata version")

    subparsers = parser.add_subparsers(dest="command")

    datasets_parser = subparsers.add_parser("datasets", help="Dataset discovery commands")
    datasets_subparsers = datasets_parser.add_subparsers(dest="datasets_command")

    datasets_list = datasets_subparsers.add_parser("list", help="List datasets")
    _ = datasets_list.add_argument("--provider", help="Filter by provider")
    _ = datasets_list.add_argument("--search", help="Filter by text search")
    _ = datasets_list.add_argument(
        "--format",
        choices=("json", "table"),
        default="table",
        help="Output format",
    )

    datasets_show = datasets_subparsers.add_parser("show", help="Show dataset metadata")
    _ = datasets_show.add_argument("dataset_id")
    _ = datasets_show.add_argument(
        "--format",
        choices=("json", "table"),
        default="table",
        help="Output format",
    )

    fetch_parser = subparsers.add_parser("fetch", help="Fetch normalized data")
    _ = fetch_parser.add_argument("dataset_id")
    _ = fetch_parser.add_argument("-p", "--param", action="append", default=[], metavar="KEY=VALUE")
    _ = fetch_parser.add_argument("--page", type=int)
    _ = fetch_parser.add_argument("--page-size", type=int)
    _ = fetch_parser.add_argument("--all", action="store_true", help="Fetch all pages")
    _ = fetch_parser.add_argument(
        "--format",
        choices=("json", "csv", "table"),
        default="table",
        help="Output format",
    )
    _ = fetch_parser.add_argument("--output", help="Write output to a file")

    raw_parser = subparsers.add_parser("raw", help="Call a raw provider operation")
    _ = raw_parser.add_argument("dataset_id")
    _ = raw_parser.add_argument("operation")
    _ = raw_parser.add_argument("-p", "--param", action="append", default=[], metavar="KEY=VALUE")
    _ = raw_parser.add_argument("--output", help="Write output to a file")

    return parser


def _configure_logging(level_name: str) -> bool:
    level_map = {
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }
    level = level_map[level_name]
    logging.basicConfig(level=level)
    root_logger = logging.getLogger("kpubdata")
    root_logger.setLevel(level)
    logger.debug("CLI logging configured", extra={"log_level": level_name.lower()})
    return level == logging.DEBUG


def _run_command(args: argparse.Namespace) -> int:
    values = vars(args)
    version_flag = cast(bool, values.get("version", False))
    command = cast(str | None, values.get("command"))
    provider_key_values = cast(list[str], values.get("provider_key", []))
    cache_enabled = cast(bool, values.get("cache", False))

    if version_flag:
        print(_get_version())
        return 0

    if command is None:
        _build_parser().print_help()
        return 0

    provider_keys = _parse_assignments(provider_key_values, flag_name="--provider-key")
    client = _create_client(cache_enabled=cache_enabled, provider_keys=provider_keys)
    try:
        if command == "datasets":
            return _handle_datasets_command(client, args)
        if command == "fetch":
            return _handle_fetch_command(client, args)
        if command == "raw":
            return _handle_raw_command(client, args)
        raise InvalidRequestError(f"Unknown command: {command}")
    finally:
        client.close()


def _create_client(*, cache_enabled: bool, provider_keys: dict[str, str]) -> Client:
    if cache_enabled:
        return Client.from_env(provider_keys=provider_keys, cache=True)
    return Client.from_env(provider_keys=provider_keys)


def _handle_datasets_command(client: Client, args: argparse.Namespace) -> int:
    values = vars(args)
    datasets_command = cast(str | None, values.get("datasets_command"))

    if datasets_command == "list":
        provider = cast(str | None, values.get("provider"))
        search_text = cast(str | None, values.get("search"))
        output_format = cast(str, values.get("format", "table"))
        datasets = client.datasets.list(provider=provider)
        if search_text:
            needle = search_text.casefold()
            datasets = [
                dataset
                for dataset in datasets
                if needle in dataset.id.casefold()
                or needle in dataset.name.casefold()
                or needle in dataset.provider.casefold()
            ]
        datasets = sorted(datasets, key=lambda dataset: dataset.id)
        if output_format == "json":
            print(
                json.dumps(
                    [_dataset_summary(dataset) for dataset in datasets],
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        dataset_rows: list[dict[str, object]] = [
            {
                "id": dataset.id,
                "name": dataset.name,
                "provider": dataset.provider,
                "operations": ", ".join(_operation_names(dataset.operations)),
            }
            for dataset in datasets
        ]
        print(_render_table(dataset_rows, headers=["id", "name", "provider", "operations"]))
        return 0

    if datasets_command == "show":
        dataset_id = cast(str, values.get("dataset_id"))
        output_format = cast(str, values.get("format", "table"))
        _, dataset = client.datasets.resolve(dataset_id)
        metadata = _dataset_details(dataset)
        if output_format == "json":
            print(json.dumps(metadata, ensure_ascii=False, indent=2))
            return 0
        raw_metadata_keys = cast(list[str], metadata["raw_metadata_keys"])
        capabilities = metadata["capabilities"]
        detail_rows: list[dict[str, object]] = [
            {"field": "id", "value": metadata["id"]},
            {"field": "name", "value": metadata["name"]},
            {"field": "provider", "value": metadata["provider"]},
            {"field": "operations", "value": ", ".join(_operation_names(dataset.operations))},
            {
                "field": "capabilities",
                "value": json.dumps(capabilities, ensure_ascii=False),
            },
            {
                "field": "raw_metadata_keys",
                "value": ", ".join(raw_metadata_keys),
            },
        ]
        print(_render_table(detail_rows, headers=["field", "value"]))
        return 0

    raise InvalidRequestError("Missing datasets subcommand")


def _handle_fetch_command(client: Client, args: argparse.Namespace) -> int:
    values = vars(args)
    params = _parse_assignments(cast(list[str], values.get("param", [])), flag_name="-p/--param")
    list_kwargs: dict[str, object] = dict(params)
    page = cast(int | None, values.get("page"))
    page_size = cast(int | None, values.get("page_size"))
    output_format = cast(str, values.get("format", "table"))
    output_path = cast(str | None, values.get("output"))
    dataset_id = cast(str, values.get("dataset_id"))
    fetch_all = cast(bool, values.get("all", False))

    if page is not None:
        list_kwargs["page"] = page
    if page_size is not None:
        list_kwargs["page_size"] = page_size

    dataset = client.dataset(dataset_id)
    if fetch_all:
        items: list[dict[str, object]] = []
        for batch in dataset.list_all(**list_kwargs):
            items.extend(batch.items)
        rendered = _render_records(items, output_format=output_format)
    else:
        batch = dataset.list(**list_kwargs)
        rendered = _render_records(batch.items, output_format=output_format)
    _write_output(rendered, output_path)
    return 0


def _handle_raw_command(client: Client, args: argparse.Namespace) -> int:
    values = vars(args)
    params = _parse_assignments(cast(list[str], values.get("param", [])), flag_name="-p/--param")
    dataset_id = cast(str, values.get("dataset_id"))
    operation = cast(str, values.get("operation"))
    output_path = cast(str | None, values.get("output"))
    dataset = client.dataset(dataset_id)
    payload = dataset.call_raw(operation, **params)
    _write_output(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), output_path)
    return 0


def _dataset_summary(dataset: DatasetRef) -> dict[str, object]:
    return {
        "id": dataset.id,
        "name": dataset.name,
        "provider": dataset.provider,
        "operations": _operation_names(dataset.operations),
    }


def _dataset_details(dataset: DatasetRef) -> dict[str, object]:
    return {
        "id": dataset.id,
        "name": dataset.name,
        "provider": dataset.provider,
        "operations": _operation_names(dataset.operations),
        "capabilities": _query_support_payload(dataset.query_support),
        "raw_metadata_keys": sorted(dataset.raw_metadata.keys()),
    }


def _query_support_payload(query_support: QuerySupport | None) -> dict[str, object] | None:
    if query_support is None:
        return None
    return {
        "pagination": query_support.pagination.value,
        "filterable_fields": sorted(query_support.filterable_fields),
        "sortable_fields": sorted(query_support.sortable_fields),
        "time_range": query_support.time_range,
        "max_page_size": query_support.max_page_size,
    }


def _render_records(items: list[dict[str, object]], *, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(_to_jsonable(items), ensure_ascii=False, indent=2)
    if output_format == "csv":
        return _render_csv(items)
    return _render_table(items, headers=_table_headers(items))


def _render_csv(items: list[dict[str, object]]) -> str:
    output = io.StringIO()
    headers = _csv_headers(items)
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    if headers:
        writer.writeheader()
        for item in items:
            writer.writerow({key: _stringify_value(item.get(key, "")) for key in headers})
    return output.getvalue()


def _render_table(rows: Sequence[Mapping[str, object]], *, headers: Sequence[str]) -> str:
    if not headers:
        return "(no columns)"
    if not rows:
        return "(no rows)"

    normalized_rows: list[dict[str, str]] = [
        {header: _truncate(_stringify_value(row.get(header, ""))) for header in headers}
        for row in rows
    ]
    widths = {
        header: max(len(header), *(len(row[header]) for row in normalized_rows))
        for header in headers
    }
    header_line = "  ".join(header.ljust(widths[header]) for header in headers)
    separator_line = "  ".join("-" * widths[header] for header in headers)
    body_lines = [
        "  ".join(row[header].ljust(widths[header]) for header in headers)
        for row in normalized_rows
    ]
    return "\n".join([header_line, separator_line, *body_lines])


def _table_headers(items: list[dict[str, object]]) -> list[str]:
    if not items:
        return []
    return list(items[0].keys())[:_MAX_TABLE_COLUMNS]


def _csv_headers(items: list[dict[str, object]]) -> list[str]:
    headers: list[str] = []
    for item in items:
        for key in item:
            if key not in headers:
                headers.append(key)
    return headers


def _parse_assignments(values: Sequence[str], *, flag_name: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for value in values:
        key, parsed_value = _split_assignment(value, flag_name=flag_name)
        assignments[key] = parsed_value
    return assignments


def _split_assignment(value: str, *, flag_name: str) -> tuple[str, str]:
    if "=" not in value:
        raise InvalidRequestError(f"{flag_name} expects KEY=VALUE: {value}")
    key, parsed_value = value.split("=", 1)
    normalized_key = key.strip()
    if not normalized_key:
        raise InvalidRequestError(f"{flag_name} expects a non-empty key: {value}")
    return normalized_key, parsed_value


def _write_output(content: str, output_path: str | None) -> None:
    if output_path is None:
        _ = sys.stdout.write(content)
        if not content.endswith("\n"):
            _ = sys.stdout.write("\n")
        return
    _ = Path(output_path).write_text(content, encoding="utf-8")


def _operation_names(operations: Iterable[Operation]) -> list[str]:
    return sorted(operation.value for operation in operations)


def _to_jsonable(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return cast(object, value.value)
    if isinstance(value, Mapping):
        mapping_value = cast(Mapping[object, object], value)
        return {str(key): _to_jsonable(item) for key, item in mapping_value.items()}
    if isinstance(value, (list, tuple)):
        sequence_value = cast(Sequence[object], value)
        return [_to_jsonable(item) for item in sequence_value]
    if isinstance(value, RecordBatch):
        return {
            "items": _to_jsonable(value.items),
            "dataset": value.dataset.id,
            "total_count": value.total_count,
            "next_page": value.next_page,
            "next_cursor": value.next_cursor,
            "meta": _to_jsonable(value.meta),
            "raw": _to_jsonable(value.raw),
        }
    if isinstance(value, DatasetRef):
        return _dataset_details(value)
    return repr(value)


def _stringify_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(_to_jsonable(value), ensure_ascii=False)


def _truncate(value: str) -> str:
    if len(value) <= _MAX_CELL_WIDTH:
        return value
    return f"{value[: _MAX_CELL_WIDTH - 1]}…"


def _print_error(exc: BaseException) -> None:
    print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)


def _get_version() -> str:
    try:
        return version("kpubdata")
    except PackageNotFoundError:
        return __version__


if __name__ == "__main__":
    exit_code = main()
    raise SystemExit(exit_code)
