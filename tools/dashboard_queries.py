"""Resolve dashboard post-process searches for independent acceptance checks."""

import configparser
from pathlib import Path


def resolve_search(form, search, seen=()):
    query = search.findtext("query") or ""
    parent = search.get("base")
    if not parent:
        return query
    if parent in seen:
        raise ValueError("Cyclic base search: " + parent)
    candidates = [
        node for node in form.findall(".//search") if node.get("id") == parent
    ]
    if len(candidates) != 1:
        raise ValueError("Missing or ambiguous base search: " + parent)
    return (
        resolve_search(form, candidates[0], seen + (parent,))
        + " | "
        + query.lstrip("| ")
    )


def isolated_query(query, scope):
    # Expand audit macro before replacing the underlying production scope.
    config = configparser.ConfigParser(interpolation=None)
    config.read(Path(__file__).resolve().parents[1] / "package/default/macros.conf")
    return (
        query.replace(
            "`vmware_vision_audit`", config["vmware_vision_audit"]["definition"]
        )
        .replace("`vmware_vision_events`", scope)
        .replace("$vc|s$", '"*"')
        .replace("$vm|s$", '"*"')
    )
