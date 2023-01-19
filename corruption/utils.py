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

from corruption.namespaces import Example









