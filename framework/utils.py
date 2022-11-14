import rdflib
from rdflib import Graph, URIRef, Literal, BNode
from pandas import DataFrame
from rdflib.plugins.sparql.processor import SPARQLResult, prepareQuery, prepareUpdate
from rdflib.namespace import FOAF, RDF, SDO, RDFS, OWL
from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

import numpy as np
from random import sample, choice
import yaml

from framework.namespaces import ErrorFOAF, ErrorRDF, ErrorSDO, Example


def sparql_results_to_df(results: SPARQLResult) -> DataFrame:
    """
    Export results from an rdflib SPARQL query into a `pandas.DataFrame`,
    using Python types. See https://github.com/RDFLib/rdflib/issues/1179.
    """
    return DataFrame(
        data=([None if x is None else x.toPython() for x in row] for row in results),
        columns=[str(x) for x in results.vars],
    )


def insert_str(string, str_to_insert, index):
    return string[:index] + str_to_insert + string[index:]


def random_replace_character(serialized_rdf, char, prob=0.5):
    char_pos = [pos for pos, c in enumerate(str(serialized_rdf)) if c == char]
    str_arr = np.array(list(str(serialized_rdf)))
    amount = int(len(char_pos) * prob)
    str_arr[sample(char_pos, amount)] = 'ERROR'
    serialized_rdf = str("".join(str_arr))
    return serialized_rdf


def print_rdf_triples(graph):
    # Loop through each triple in the graph (subj, pred, obj)
    for subj, pred, obj in graph:
        # Check if there is at least one triple in the Graph
        if (subj, pred, obj) not in graph:
            raise Exception("No triple found!")
        else:
            print(subj, pred, obj)

def read_config(config_filepath):
    with open(config_filepath, 'r') as stream:
        try:
            parsed_yaml=yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return parsed_yaml


def construct_error_example_graph():
    g = Graph()
    g.bind("foaf", FOAF)
    g.bind("error_foaf", ErrorFOAF)
    g.bind("sdo", SDO)
    g.bind("error_sdo", ErrorSDO)

    bob = URIRef("http://example.org/people/Bob")
    linda = URIRef("http://example.org/people/Linda")
    error_hans = URIRef("http://exampleorg/Hans")

    g.add((bob, RDF.type, FOAF.Person))
    g.add((bob, FOAF.name, Literal("Bob")))
    g.add((bob, ErrorFOAF.age, Literal(24)))
    g.add((bob, FOAF.knows, linda))
    g.add((linda, RDF.type, FOAF.Person))
    g.add((linda, FOAF.name, Literal("Linda")))
    g.add((error_hans, RDF.type, ErrorSDO.HumAn))
    g.add((error_hans, ErrorSDO.name, Literal("Hans")))
    return g

def construct_example_graph():
    g = Graph()
    g.bind("foaf", FOAF)
    g.bind("sdo", SDO)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)
    g.bind("ex", Example)

    dennis = URIRef("http://example.org/Dennis")

    g.add((dennis, RDF.type, Example.Person))

    #g.add((Example.Group, Example.hasMember, dennis))
    g.add((dennis, Example.hasAddress, Example.Address))

    g.add((Example.hasMember, RDFS.range, Example.Person))
    g.add((Example.hasAddress, RDFS.domain, Example.Person))

    return g


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
        initNs = { "rdf": RDF },
        initBindings = bindings
    )
    df = sparql_results_to_df(qres)
    return df


def sparql_update_object(graph, subject, predicate, object, target_object):
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
            initNs = { "rdf": RDF },
            initBindings = {"s": subject, "p": predicate, "o": object, "to": target_object}
        )
    return graph

def sparql_update_subject(graph, subject, predicate, object, target_subject):
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
            initNs = { "rdf": RDF },
            initBindings = {"s": subject, "p": predicate, "o": object, "ts": target_subject}
    )
    return graph