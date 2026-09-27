from __future__ import annotations

import unicodedata
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse


SANCTIONS_JURISDICTIONS = ("OFAC", "UN", "EU", "UK")
SANCTIONS_SOURCE_HOSTS = {
    "OFAC": ("treasury.gov",),
    "UN": ("un.org", "unsolprodfiles.blob.core.windows.net"),
    "EU": ("europa.eu",),
    "UK": ("gov.uk", "fcdo.gov.uk"),
}
UNAVAILABLE_SANCTIONS_SOURCE = {
    "status": "unavailable",
    "records": [],
    "source_url": None,
    "updated_at": None,
}
_sanctions_source_providers: dict[str, Callable[[], dict[str, Any]]] = {}
_counterparty_registry_providers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}


def register_sanctions_source(
    jurisdiction: str,
    provider: Callable[[], dict[str, Any]],
) -> None:
    key = jurisdiction.upper()
    if key not in SANCTIONS_JURISDICTIONS:
        raise ValueError(f"Unsupported sanctions jurisdiction: {jurisdiction}")
    _sanctions_source_providers[key] = provider


def register_counterparty_registry(
    country: str,
    provider: Callable[[dict[str, Any]], dict[str, Any]],
) -> None:
    if not country.strip():
        raise ValueError("Country is required to register a company registry provider")
    _counterparty_registry_providers[country.casefold()] = provider


def normalize_entity_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    normalized = normalized.replace("&", " and ")
    characters = (
        character
        if unicodedata.category(character)[0] in {"L", "N"}
        else " "
        for character in normalized
        if not unicodedata.combining(character)
    )
    return " ".join("".join(characters).split())


def _entity_names(entity: dict[str, Any]) -> set[str]:
    aliases = entity.get("aliases", [])
    names = [entity.get("name", "")]
    if isinstance(aliases, list):
        names.extend(aliases)
    return {normalize_entity_name(name) for name in names if isinstance(name, str) and name.strip()}


def _has_https_source(source_url: Any, allowed_hosts: tuple[str, ...] | None = None) -> bool:
    if not isinstance(source_url, str):
        return False
    parsed = urlparse(source_url)
    hostname = (parsed.hostname or "").casefold()
    return (
        parsed.scheme == "https"
        and bool(hostname)
        and (allowed_hosts is None or any(hostname == host or hostname.endswith(f".{host}") for host in allowed_hosts))
    )


def _is_recent_check(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        checked_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if checked_at.tzinfo is None:
        return False
    age = datetime.now(timezone.utc) - checked_at.astimezone(timezone.utc)
    return timedelta(0) <= age <= timedelta(hours=24)


def _is_valid_source_date(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def screen_sanctions(
    entity: dict[str, Any],
    source_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    names = _entity_names(entity)
    if source_results is None:
        source_results = {}
        for jurisdiction in SANCTIONS_JURISDICTIONS:
            provider = _sanctions_source_providers.get(jurisdiction)
            if provider is None:
                source_results[jurisdiction] = UNAVAILABLE_SANCTIONS_SOURCE
                continue
            try:
                source_results[jurisdiction] = provider()
            except Exception as error:
                source_results[jurisdiction] = {
                    **UNAVAILABLE_SANCTIONS_SOURCE,
                    "error": type(error).__name__,
                }
    sources = source_results
    matches: list[dict[str, Any]] = []
    source_status: dict[str, dict[str, Any]] = {}

    for jurisdiction in SANCTIONS_JURISDICTIONS:
        source = sources.get(jurisdiction, UNAVAILABLE_SANCTIONS_SOURCE)
        if not isinstance(source, dict):
            source = UNAVAILABLE_SANCTIONS_SOURCE
        status = source.get("status", "unavailable")
        source_status[jurisdiction] = {
            "status": "unavailable",
            "source_url": source.get("source_url"),
            "updated_at": source.get("updated_at"),
            "checked_at": source.get("checked_at"),
        }
        if status != "available":
            continue
        records = source.get("records", [])
        if (
            not _has_https_source(source.get("source_url"), SANCTIONS_SOURCE_HOSTS[jurisdiction])
            or not _is_valid_source_date(source.get("updated_at"))
            or not _is_recent_check(source.get("checked_at"))
            or not isinstance(records, list)
            or not records
        ):
            continue
        if any(
            not isinstance(record, dict)
            or not isinstance(record.get("names"), list)
            or not any(isinstance(name, str) and name.strip() for name in record["names"])
            or any(not isinstance(name, str) for name in record["names"])
            for record in records
        ):
            continue
        source_status[jurisdiction]["status"] = "available"
        for record in records:
            listed_names = {
                normalize_entity_name(value)
                for value in record.get("names", [])
                if isinstance(value, str) and value.strip()
            }
            matched_names = sorted(names & listed_names)
            if matched_names:
                matches.append({
                    "jurisdiction": jurisdiction,
                    "matched_names": matched_names,
                    "list_id": record.get("list_id"),
                    "source_url": source.get("source_url"),
                    "updated_at": source.get("updated_at"),
                })

    all_sources_available = all(source_status[name]["status"] == "available" for name in SANCTIONS_JURISDICTIONS)
    if matches:
        status = "potential_match"
    elif all_sources_available:
        status = "no_match_found"
    else:
        status = "inconclusive"

    if not names:
        status = "inconclusive"

    return {
        "screening_status": status,
        "entity_name": entity.get("name"),
        "matches": matches,
        "source_status": source_status,
        "coverage_complete": all_sources_available,
        "limitations": [
            "Name screening is not a legal determination or a substitute for ownership/control analysis.",
            "Matching uses normalized exact names and supplied aliases; transliteration, fuzzy matching, and ownership/control are not covered.",
            "No match is meaningful only for the listed sources and their recorded update times.",
        ],
        "matching_method": "unicode-normalized exact name and alias matching",
    }


def verify_counterparty(
    entity: dict[str, Any],
    registry_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if registry_result is None or not isinstance(registry_result, dict):
        country = entity.get("country")
        provider = _counterparty_registry_providers.get(country.casefold()) if isinstance(country, str) else None
        if provider:
            try:
                registry_result = provider(entity)
            except Exception as error:
                return {
                    "identity_status": "unavailable",
                    "entity_name": entity.get("name"),
                    "jurisdiction": country,
                    "registration_number": entity.get("registration_number"),
                    "registry_source": None,
                    "verified_fields": [],
                    "limitations": [f"Official registry lookup failed ({type(error).__name__})."],
                }

    if registry_result is None:
        return {
            "identity_status": "unavailable",
            "entity_name": entity.get("name"),
            "jurisdiction": entity.get("country"),
            "registration_number": entity.get("registration_number"),
            "registry_source": None,
            "verified_fields": [],
            "limitations": ["No verified official company-registry adapter is configured for this jurisdiction."],
        }

    required_fields = ("legal_name", "country", "registration_number", "registry_source", "source_url", "checked_at")
    if not _has_https_source(registry_result.get("source_url")) or not _is_recent_check(registry_result.get("checked_at")):
        return {
            "identity_status": "partial",
            "entity_name": entity.get("name"),
            "jurisdiction": registry_result.get("country", entity.get("country")),
            "registration_number": registry_result.get("registration_number"),
            "legal_name": registry_result.get("legal_name"),
            "registry_source": registry_result.get("registry_source"),
            "source_url": registry_result.get("source_url"),
            "verified_fields": [],
            "limitations": ["Registry evidence must include an HTTPS source URL and a lookup time within 24 hours before identity can be marked verified."],
        }
    verified_fields = [field for field in required_fields if registry_result.get(field)]
    complete = all(registry_result.get(field) for field in required_fields)
    supplied_names = _entity_names(entity)
    registered_name = registry_result.get("legal_name")
    supplied_registration = entity.get("registration_number")
    registered_registration = registry_result.get("registration_number")
    name_matches = isinstance(registered_name, str) and normalize_entity_name(registered_name) in supplied_names
    registration_matches = (
        isinstance(supplied_registration, str)
        and bool(supplied_registration.strip())
        and isinstance(registered_registration, str)
        and supplied_registration.strip().casefold() == registered_registration.strip().casefold()
    )
    name_conflict = bool(supplied_names) and not name_matches
    registration_conflict = bool(supplied_registration) and not registration_matches
    supplied_country = entity.get("country")
    registered_country = registry_result.get("country")
    country_conflict = (
        isinstance(supplied_country, str)
        and bool(supplied_country.strip())
        and isinstance(registered_country, str)
        and supplied_country.strip().casefold() != registered_country.strip().casefold()
    )
    identity_matches = (name_matches or registration_matches) and not name_conflict and not registration_conflict
    if country_conflict or name_conflict or registration_conflict or (complete and not identity_matches):
        return {
            "identity_status": "conflicting",
            "entity_name": entity.get("name"),
            "jurisdiction": registry_result.get("country", entity.get("country")),
            "registration_number": registered_registration,
            "legal_name": registered_name,
            "registry_source": registry_result.get("registry_source"),
            "source_url": registry_result.get("source_url"),
            "verified_fields": verified_fields,
            "limitations": ["The official registry result does not match the supplied name or registration number."],
        }
    return {
        "identity_status": "verified" if complete and identity_matches else "partial",
        "entity_name": entity.get("name"),
        "jurisdiction": registry_result.get("country", entity.get("country")),
        "registration_number": registry_result.get("registration_number"),
        "legal_name": registry_result.get("legal_name"),
        "registry_source": registry_result.get("registry_source"),
        "source_url": registry_result.get("source_url"),
        "checked_at": registry_result.get("checked_at"),
        "verified_fields": verified_fields,
        "matched_on": "registration_number" if registration_matches else "legal_name" if name_matches else None,
        "limitations": ["Registry identity verification does not establish creditworthiness or sanctions clearance."],
    }