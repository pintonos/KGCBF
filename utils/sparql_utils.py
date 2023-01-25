import subprocess
import rdflib
from rdflib import Literal
from rdflib.namespace import RDF, RDFS
from rdflib.plugins.sparql.processor import SPARQLResult

from pandas import DataFrame


def sparql_results_to_df(results: SPARQLResult) -> DataFrame:
    """
    Export results from an rdflib SPARQL query into a `pandas.DataFrame`,
    using Python types. See https://github.com/RDFLib/rdflib/issues/1179.
    """
    return DataFrame(
        data=([None if x is None else x.toPython() for x in row] for row in results),
        columns=[str(x) for x in results.vars],
    )


def sparql_query(graph, subject, predicate, object):
    bindings = {"s": subject, "p": predicate, "o": object}
    bindings = {k: v for k, v in bindings.items() if v is not None}
    qres = graph.query(
        """
        SELECT ?s ?p ?o
        WHERE {
            ?s ?p ?o .
        }
        """,
        initNs={"rdf": RDF},
        initBindings=bindings
    )
    df = sparql_results_to_df(qres)
    return df


def update_predicate(graph, subject, predicate, object, target_predicate):
    try:
        valid_uri = rdflib.term._is_valid_uri(object)
        if valid_uri:
            __sparql_update_predicate(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), rdflib.URIRef(object),
                                  rdflib.URIRef(target_predicate))
        else:
            __sparql_update_predicate(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), Literal(object),
                                  rdflib.URIRef(target_predicate))
    except:
        __sparql_update_predicate(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), Literal(object),
                                  rdflib.URIRef(target_predicate))


def __sparql_update_predicate(graph, subject, predicate, object, target_predicate):
    graph.update(
        """DELETE {
                ?s ?p ?o .
            }
            INSERT {
                ?s ?tp ?o .
            }
            WHERE {
                ?s ?p ?o .
            }""",
        initNs={"rdf": RDF},
        initBindings={"s": subject, "p": predicate, "o": object, "tp": target_predicate}
    )
    return graph


def update_object(graph, subject, predicate, object, target_object):
    try: # int and float values bug in _is_valid_uri
        valid_uri = rdflib.term._is_valid_uri(object)
        if valid_uri:
            __sparql_update_object(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), rdflib.URIRef(object),
                                rdflib.URIRef(target_object))
        else:
            __sparql_update_object(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), Literal(object),
                           rdflib.URIRef(target_object))
    except:
        __sparql_update_object(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), Literal(object),
                           rdflib.URIRef(target_object))


def __sparql_update_object(graph, subject, predicate, object, target_object):
    graph.update(
        """DELETE {
                ?s ?p ?o .
            }
            INSERT { 
                ?s ?p ?to . 
            }
            WHERE {
                ?s ?p ?o .
            }""",
        initNs={"rdf": RDF},
        initBindings={"s": subject, "p": predicate, "o": object, "to": target_object}
    )
    return graph


def update_subject(graph, subject, predicate, object, target_subject):
    try:  # int and float values bug in _is_valid_uri
        valid_uri = rdflib.term._is_valid_uri(object)
        if valid_uri:
            __sparql_update_subject(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), rdflib.URIRef(object),
                                    rdflib.URIRef(target_subject))
        else:
            __sparql_update_subject(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), Literal(object),
                                    rdflib.URIRef(target_subject))
    except:
        __sparql_update_subject(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), Literal(object),
                                rdflib.URIRef(target_subject))


def __sparql_update_subject(graph, subject, predicate, object, target_subject):
    graph.update(
        """DELETE {
                ?s ?p ?o .
            }
            INSERT { 
                ?ts ?p ?o . 
            }
            WHERE {
                ?s ?p ?o .
            }""",
        initNs={"rdf": RDF},
        initBindings={"s": subject, "p": predicate, "o": object, "ts": target_subject}
    )
    return graph


def get_triple_count(graph):
    """
    Get the count of triples in the KG, not containing rdf:type declarations.
    """
    qres = graph.query(
        """
        SELECT (count(?p) as ?count)
        WHERE {
            [] ?p [] .
            FILTER (?p != rdf:type).
        }
        """)
    return int(next(iter(qres))[0])


def get_all_instance_ids(graph):
    qres = graph.query(
        """
        SELECT ?s ?p ?o
        WHERE {
            ?s ?p ?o .
            FILTER EXISTS { ?s rdf:type ?o2 }
            OPTIONAL { ?s rdf:type ?o }
        }
        """,
        initNs={"rdf": RDF}
    )
    df = sparql_results_to_df(qres)
    return df


def get_all_instance_declarations(graph):
    qres = graph.query(
        """
        SELECT ?s ?p ?o
        WHERE {
            ?s ?p ?o .
            FILTER(?p = rdf:type)
        }
        """,
        initNs={"rdf": RDF}
    )
    df = sparql_results_to_df(qres)
    return df





def get_subject_only_entities_with_count(graph):
    qres = graph.query(
        """
        SELECT ?s ?o ?count
        WHERE {
            ?s rdf:type ?o
            FILTER NOT EXISTS { [] ?p3 ?s }
            {
                SELECT (count(?p) AS ?count)
                WHERE 
                {
                    ?s ?p []
                    FILTER(?p != rdf:type)
                }
            } 
        }
        HAVING ( ?count > 0 )
        """,
        initNs={"rdf": RDF}
    )
    df = sparql_results_to_df(qres)
    return df


def get_object_only_entities_with_count(graph):
    qres = graph.query(
        """
        SELECT ?s ?o ?count
        WHERE {
            ?s rdf:type ?o
            FILTER NOT EXISTS 
            {
                ?s ?p1 []
                FILTER (?p1 != rdf:type)
            }
            {
                SELECT (count(?p) AS ?count)
                WHERE 
                {
                    [] ?p ?s
                    FILTER(?p != rdf:type)
                }
            } 
        }
        HAVING ( ?count > 0 )
        """
        ,
        initNs={"rdf": RDF}
    )
    df = sparql_results_to_df(qres)
    return df


def get_properties(graph):
    qres = graph.query(
        """
        SELECT ?s ?p ?o
        WHERE {
            ?s ?p ?o .
            FILTER ( ?p != rdf:type)
        }
        """,
        initNs={"rdf": RDF}
    )
    df = sparql_results_to_df(qres)
    return df


def build_level_query(levels=1):
    assert levels <= 3, "Sampling a subgraph with levels > 3 is not supported."
    construct_str = ""
    where_str = ""
    for l in range(1, levels + 1):
        construct_str = construct_str + f"""
            ?s{l} ?p{l} ?o{l} .
            ?s{l}s ?p{l}s ?s{l} ."""
        if l == 1:
            where_str = where_str + f"""
                {{?s{l} ?p{l} ?o{l} FILTER (?s1 = ?init_instance) .}}
                UNION
                {{?s{l}b ?p{l}b ?s{l} FILTER (?s1 = ?init_instance) .}}
                BIND (?o{l} as ?s{l + 1}) ."""
        else:
            where_str = where_str + f"""
                ?s{l} ?p{l} ?o{l} .
                ?s{l}b ?p{l}b ?s{l} .
                BIND (?o{l} as ?s{l + 1}) ."""

    query_str = """
        CONSTRUCT {""" + construct_str + """
        }
        WHERE {""" + where_str + """
        }
    """
    # print(query_str)
    return query_str


def get_domain_range_assertions(graph):
    qres = graph.query(
        """
        CONSTRUCT {
            ?s ?p ?o .
        }
        WHERE {
            ?s ?p ?o .
            FILTER (?p = rdfs:domain || ?p = rdfs:range)
        }
        """,
        initNs={"rdfs": RDFS}
    )
    return qres.graph