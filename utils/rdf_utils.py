import rdflib
import yaml
import subprocess
from rdflib import Graph, Literal
from rdflib.namespace import BRICK, CSVW, DC, DCAT, DCMITYPE, DCTERMS, DCAM, DOAP, FOAF, ODRL2, ORG, OWL, PROF, PROV, \
    QB, RDF, RDFS, SDO, SH, SKOS, SOSA, SSN, TIME, VANN, VOID, WGS, XSD
from rdflib.term import URIRef

from corruption.namespaces import Example
from utils.sparql_utils import get_all_instance_ids, get_domain_range_assertions, build_level_query

def print_rdf_triples(graph):
    # Loop through each triple in the graph (subj, pred, obj)
    for subj, pred, obj in graph:
        # Check if there is at least one triple in the Graph
        if (subj, pred, obj) not in graph:
            raise Exception("No triple found!")
        else:
            print(subj, pred, obj)


def get_shacl_from_ontology(ontology_file):
    # requires shaclinfer to be installed and reachable by the default system CLI
    # https://github.com/TopQuadrant/shacl
    subprocess.run(
        f"shaclinfer -datafile {ontology_file} -shapesfile owl2sh.ttl > data/ontology_shacl.ttl",
        shell=True)


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

    #print(subgraph.serialize(format="turtle"))
    return subgraph