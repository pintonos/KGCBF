import rdflib
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.plugins.sparql.processor import SPARQLResult, prepareQuery, prepareUpdate
from rdflib.namespace import FOAF, RDF, SDO
from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

from pandas import DataFrame
import random

from framework.utils import insert_str, sparql_results_to_df, sparql_query, sparql_update_object, sparql_update_subject


class AbstractError():
    def __init__(self):
        self.id = None
        self.name = None
        self.logger = None

    def update_graph(self):
        raise NotImplementedError

    def find_error(self):
        raise NotImplementedError

    def __str__(self):
        return (
            self.name
        )


class DomainTypeError(AbstractError):
    def __init__(self, prob, logger):
        super(DomainTypeError, self).__init__()
        self.name = "Domain Violation"
        self.prob = prob
        self.logger = logger

    def get_subject_only_entities(self, graph):
        qres = graph.query(
            """
            SELECT ?s ?o
            WHERE {
                ?s rdf:type ?o .
                FILTER NOT EXISTS { [] ?p ?s } .
            }
            """,
            initNs = { "rdf": RDF }
        )
        df = sparql_results_to_df(qres)
        return df

    def update_graph(self, graph):
        subjects_only = self.get_subject_only_entities(graph)
        amount = int(len(subjects_only) * self.prob)
        sampled = subjects_only.loc[random.sample(list(subjects_only.index), amount)]
        sampled_s, sampled_o = sampled.s.tolist(), sampled.o.tolist()
        for s, o in zip(sampled_s, sampled_o):
            corr_o = str(random.choice(dir(SDO)))
            sparql_update_object(graph, rdflib.URIRef(s), RDF.type, rdflib.URIRef(o), rdflib.URIRef(corr_o)) # random SDO type for now
            self.logger.log_error('change_domain', s, o, corr_o)
        
        return graph


class RangeTypeError(AbstractError):
    def __init__(self, prob, logger):
        super(RangeTypeError, self).__init__()
        self.name = "Range Violation"
        self.prob = prob
        self.logger = logger

    def get_object_only_entities(self, graph):
        qres = graph.query(
            """
            SELECT ?s ?o
            WHERE {
                ?s rdf:type ?o .
                FILTER NOT EXISTS { ?o ?p [] } .
            }
            """,
            initNs = { "rdf": RDF }
        )
        df = sparql_results_to_df(qres)
        print(df)
        return df

    def update_graph(self, graph):
        objects_only = self.get_object_only_entities(graph)
        amount = int(len(objects_only) * self.prob)
        sampled = objects_only.loc[random.sample(list(objects_only.index), amount)]
        sampled_s, sampled_o = sampled.s.tolist(), sampled.o.tolist()
        for s, o in zip(sampled_s, sampled_o):
            corr_o = str(random.choice(dir(SDO)))
            sparql_update_object(graph, rdflib.URIRef(s), RDF.type, rdflib.URIRef(o), rdflib.URIRef(corr_o)) # random SDO type for now
            self.logger.log_error('change_range', s, o, corr_o)
        
        return graph


class WrongInstanceError(AbstractError):
    def __init__(self, prob):
        super(WrongInstanceError, self).__init__()
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
