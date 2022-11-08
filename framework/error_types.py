import rdflib
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.plugins.sparql.processor import SPARQLResult, prepareQuery, prepareUpdate
from rdflib.namespace import FOAF, RDF, SDO
from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

from pandas import DataFrame
import random

from framework.utils import insert_str, sparql_results_to_df


class GeneralErrorType():
    def __init__(self):
        self.id = None
        self.name = None

    def update_graph(self):
        raise NotImplementedError

    def __str__(self):
        return (
            self.name
        )


class DomainErrorType(GeneralErrorType):
    def __init__(self, prob):
        super(DomainErrorType, self).__init__()
        self.name = "Domain Violation"
        self.prob = prob

    def get_type_asserts(self, graph, prob):
        qres = graph.query(
            """
            SELECT ?s ?o
            WHERE {
                ?s rdf:type ?o .
            }
            """,
            initNs = { "rdf": RDF }
        )

        type_asserts = sparql_results_to_df(qres)
        amount = int(len(type_asserts) * prob)
        sampled_type_asserts = type_asserts.loc[random.sample(list(type_asserts.index), amount)]
        return sampled_type_asserts.s.tolist(), sampled_type_asserts.o.tolist()

    def update_type_assert(self, graph, subject, object, target_uri):
        q = prepareUpdate(
            """DELETE {
                ?subject rdf:type ?object .
            }
            INSERT { 
                ?subject rdf:type ?target_uri . 
            }
            WHERE {
                ?subject rdf:type ?object .
            }""",
            initNs = { "rdf": RDF }
        )
        graph.update(q, initBindings={'subject': rdflib.URIRef(subject), 'object': rdflib.URIRef(object), 'target_uri': target_uri})
        return graph

    def update_graph(self, graph):
        s_type_asserts, o_type_asserts = self.get_type_asserts(graph, self.prob)
        print(s_type_asserts)
        for s, o in zip(s_type_asserts, o_type_asserts):
            graph = self.update_type_assert(graph, s, o, random.choice(dir(SDO))) # random SDO type for now
        
        return graph


class WrongInstanceErrorType1(GeneralErrorType):
    def __init__(self, prob):
        super(WrongInstanceErrorType1, self).__init__()
        self.name = "not a proper instance identifier"
        self.prob = prob

    def update_instance_id(self, graph, source_id, target_id):
        q = prepareUpdate(
            """DELETE {
                ?source_id ?p ?o .
            }
            INSERT { 
                ?target_id ?p ?o . 
            }
            WHERE {
                ?source_id ?p ?o .
            }""",
        )
        graph.update(q, initBindings={'source_id': rdflib.URIRef(source_id), 'target_id': rdflib.URIRef(target_id)})
        return graph

    def get_instance_ids(self, graph, prob):
        qres = graph.query(
                """
                SELECT DISTINCT ?s
                WHERE {
                    ?s ?p ?o .
                }
                """
            )

        instance_ids = sparql_results_to_df(qres)
        amount = int(len(instance_ids) * prob)
        return instance_ids.loc[random.sample(list(instance_ids.index), amount)].s.tolist()

    def update_graph(self, graph):
        sampled_instance_ids = self.get_instance_ids(graph, self.prob)
        target = insert_str(sampled_instance_ids[0], "Ä", 1)
        print(target)
        graph = self.update_instance_id(graph, sampled_instance_ids[0], target)
        
        return graph
