import re

import yaml
from rdflib import Graph

from corruption.logger import Logger


def matching_regex_count(content: str, query: str) -> int:
    """
    Returns the number of matching regex expression in the content.
    @param content: The content to check for regex expressions.
    @param query: The regex query.
    @return: The number of matching expressions.
    """
    return len(re.findall(query, content))


def matching_graph_count(graph: Graph, query: str) -> int:
    """
    Returns the number of matching SPARQL expressions in the knowledge graph.
    @param graph: The knowledge graph (rdflib graph).
    @param query: The SPARQL query.
    @return: The number of matching expressions.
    """
    return len(graph.query(query))


def fill_approach_dictionary_placeholders(query: str, error: dict, regex_escape: bool) -> str:
    """
    Replaces the placeholders in an approach dictionary query according to the given error.
    @param query: The query (containing placeholders) which is used to detect a given error.
    @param error: An error as logged in the error_log, containing the original and corrupted triple.
    @param regex_escape: Whether to escape the string for regex.
    @return: A query without placeholders which can be used to test if an approach has detected an error.
    """
    query = query.replace("$original.subject$", encode_uri(error['original']['s'], regex_escape))
    query = query.replace("$original.predicate$", encode_uri(error['original']['p'], regex_escape))
    query = query.replace("$original.object$", encode_uri(error['original']['o'], regex_escape))
    query = query.replace("$corrupt.subject$", encode_uri(error['corrupted']['s'], regex_escape))
    query = query.replace("$corrupt.predicate$", encode_uri(error['corrupted']['p'], regex_escape))
    query = query.replace("$corrupt.object$", encode_uri(error['corrupted']['o'], regex_escape))
    return query


def encode_uri(uri: str, regex_escape: bool) -> str:
    """
    Encodes a unique resource identifier string.
    @param uri: The name of a unique resource identifier.
    @param regex_escape: Whether to escape the string for regex.
    @return: The encoded string.
    """
    return f"<{uri}>" if not regex_escape else re.escape(f"<{uri}>")