import rdflib
from rdflib import Graph, URIRef, Literal, BNode
from pandas import DataFrame
from rdflib.plugins.sparql.processor import SPARQLResult, prepareQuery, prepareUpdate
from rdflib.namespace import FOAF, RDF, SDO
from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef


class Example(DefinedNamespace):
    _NS = Namespace("http://example.org/")
    
