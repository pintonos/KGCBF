import rdflib
from rdflib import Graph, URIRef, Literal, BNode
from pandas import DataFrame
from rdflib.plugins.sparql.processor import SPARQLResult, prepareQuery, prepareUpdate
from rdflib.namespace import FOAF, RDF, SDO
from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef


class ErrorRDF(RDF):
    _NS = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-nsERROR#")

class ErrorFOAF(FOAF):
    _NS = Namespace("http://xmlns.com/foaf/0.1/ERROR/")

class ErrorSDO(SDO):
    _NS = Namespace("https://schema.org/ERROR/")

    Human: URIRef 
    HumAn: URIRef 
    homeAddress: URIRef

class Example(DefinedNamespace):
    _NS = Namespace("http://example.org/")

    Address: URIRef
    DAddress: URIRef 
    addressDoor: URIRef

    Person: URIRef
    Group: URIRef
    hasMember: URIRef
    hasAddress: URIRef
    
