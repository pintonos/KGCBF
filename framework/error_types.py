import rdflib
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.plugins.sparql.processor import SPARQLResult, prepareQuery, prepareUpdate
from rdflib.namespace import FOAF, RDF, SDO
from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

from pandas import DataFrame
from random import sample

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
            #initNs = { "foaf": FOAF }
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
        return instance_ids.loc[sample(list(instance_ids.index), amount)].s.tolist()

    def update_graph(self, graph):
        sampled_instance_ids = self.get_instance_ids(graph, self.prob)
        target = insert_str(sampled_instance_ids[0], "Ä", 1)
        print(target)
        graph = self.update_instance_id(graph, sampled_instance_ids[0], target)
        
        return graph
