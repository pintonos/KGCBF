import random
import subprocess
from random import sample

import numpy as np
import rdflib
import yaml
from pandas import DataFrame
from rdflib import Graph, Literal
from rdflib.namespace import BRICK, CSVW, DC, DCAT, DCMITYPE, DCTERMS, DCAM, DOAP, FOAF, ODRL2, ORG, OWL, PROF, PROV, \
    QB, RDF, RDFS, SDO, SH, SKOS, SOSA, SSN, TIME, VANN, VOID, WGS, XSD
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


def find_init_instances(graph, size):
    all_instance_ids = get_all_instance_ids(graph)
    counts = all_instance_ids['s'].value_counts()  # or 'o'?
    normalized_counts = (counts - counts.min()) / (counts.sum() - counts.min())

    init_instances = []
    reached_size = 0.0
    while reached_size <= size:
        sampled_instance = normalized_counts.sample(n=1)
        if sampled_instance.values[0] > 0:
            init_instances.append(rdflib.URIRef(sampled_instance.index[0]))
            reached_size += sampled_instance.values[0]
    # remove duplicates
    init_instances = list(set(init_instances))
    return init_instances


def bind_all_namespaces(graph):
    namespaces = [BRICK, CSVW, DC, DCAT, DCMITYPE, DCTERMS, DCAM, DOAP, FOAF, ODRL2, ORG, OWL, PROF, PROV, QB, RDF,
                  RDFS, SDO, SH, SKOS, SOSA, SSN, TIME, VANN, VOID, WGS, XSD]
    namespaces_str = ['brick', 'csvw', 'cv', 'dcat', 'dcmitype', 'dcterms', 'dcam', 'doap', 'foaf', 'odrl2', 'org',
                      'owl', 'prof', 'prov', 'qb', 'rdf', 'rdfs', 'sdo', 'sh', 'skos', 'sosa', 'ssn', 'time', 'vann',
                      'void', 'wgs', 'xsd']
    for i, ns in enumerate(namespaces):
        graph.bind(namespaces_str[i], ns)
    return graph


def extract_subgraph(graph, size=0.5, levels=1, bind_namespaces=True):
    init_instances = find_init_instances(graph, size)
    subgraph = Graph()
    for init_instance in init_instances:
        subgraph += graph.query(
            build_level_query(levels=levels),
            initBindings={'init_instance': init_instance}
        ).graph
    subgraph += get_domain_range_assertions(graph)
    if bind_namespaces:
        subgraph = bind_all_namespaces(subgraph)
        subgraph.bind("example", Example)

    print(subgraph.serialize(format="turtle"))
    return subgraph
