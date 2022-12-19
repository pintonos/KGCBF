import random
import subprocess
from random import sample

import numpy as np
import rdflib
import yaml
from pandas import DataFrame
from rdflib import Graph, Literal
from rdflib.namespace import FOAF, RDF, SDO, RDFS, OWL
from rdflib.plugins.sparql.processor import SPARQLResult
from rdflib.term import URIRef

from framework.namespaces import Example


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
    if index == -1:
        return string + str_to_insert
    return string[:index] + str_to_insert + string[index:]


def get_random_special_characters(length=1):
    special_chars = ["$", "&", "%", "*", "§", "Ä", "Ö", "Ü", ";"]
    random_char_list = random.sample(special_chars, length)
    return "".join(random_char_list)


def get_random_characters(length=1):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    random_char_list = random.sample(chars, length)
    return "".join(random_char_list)


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
            parsed_yaml = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return parsed_yaml


def get_namespace_from_uri(graph, uri):
    namespaces = [RDF, RDFS, FOAF, SDO, OWL, Example]
    extracted_ns = graph.compute_qname(URIRef(uri))[1]
    for ns in namespaces:
        if ns._NS == extracted_ns:
            return ns


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

    # g.add((Example.Group, Example.hasMember, dennis))
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
        initNs={"rdf": RDF},
        initBindings=bindings
    )
    df = sparql_results_to_df(qres)
    return df


def update_predicate(graph, subject, predicate, object, target_predicate):
    if rdflib.term._is_valid_uri(object):
        __sparql_update_predicate(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), rdflib.URIRef(object),
                                  rdflib.URIRef(target_predicate))
    else:
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
    __sparql_update_object(graph, rdflib.URIRef(subject), rdflib.URIRef(predicate), rdflib.URIRef(object),
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


def get_shacl_from_ontology(ontology_file):
    # requires shaclinfer to be installed and reachable by the default system CLI
    # https://github.com/TopQuadrant/shacl
    subprocess.run(
        f"shaclinfer -datafile {ontology_file} -shapesfile owl2sh.ttl > data/ontology_shacl.ttl",
        shell=True)


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


def get_invalid_characters():
    return "<>{}|\\^`\""


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
