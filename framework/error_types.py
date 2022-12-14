import uuid

import numpy as np
import rdflib
from rdflib.plugins.sparql.processor import prepareUpdate
from rdflib.namespace import RDF, SDO

import random

from framework.utils import *


class AbstractError:
    def __init__(self):
        self.id = None
        self.name = None
        self.logger = None

    def update_graph(self, graph):
        raise NotImplementedError

    def post_process(self, file):
        raise NotImplementedError

    def __str__(self):
        return (
            self.name
        )


class SemanticSyntacticInstanceIdentifierError(AbstractError):
    def __init__(self, prob, logger):
        super(SemanticSyntacticInstanceIdentifierError, self).__init__()
        self.name = "Semantic Syntactic Instance Identifier Violation"
        self.prob = prob
        self.logger = logger

    def update_graph(self, graph):
        subjects_only = get_all_instance_ids(graph)
        unique_subjects = subjects_only["s"].unique()
        amount = int(len(unique_subjects) * self.prob)
        sampled_subjects = random.sample(list(unique_subjects), amount)

        for subject in sampled_subjects:
            triples = subjects_only.loc[subjects_only['s'] == subject]
            chars = get_random_characters(length=5)
            for triple in triples.iterrows():
                s = triple[1]["s"]
                p = triple[1]["p"]
                o = triple[1]["o"]
                target = insert_str(s, chars, -1)
                try:  # int and float values bug in _is_valid_uri
                    valid_uri = rdflib.term._is_valid_uri(o)
                    if valid_uri:
                        sparql_update_subject(graph, rdflib.URIRef(s), rdflib.URIRef(p), rdflib.URIRef(o),
                                              rdflib.URIRef(target))
                    else:
                        sparql_update_subject(graph, rdflib.URIRef(s), rdflib.URIRef(p), Literal(o),
                                              rdflib.URIRef(target))
                except:
                    sparql_update_subject(graph, rdflib.URIRef(s), rdflib.URIRef(p), Literal(o), rdflib.URIRef(target))

                self.logger.log_error('corrupt_instance_id', s, s, target, "semantic-syntactic")

        return graph

    def post_process(self, file):
        pass


class SyntacticInstanceIdentifierError(AbstractError):
    def __init__(self, prob, logger):
        super(SyntacticInstanceIdentifierError, self).__init__()
        self.name = "Syntactic Instance Identifier Violation"
        self.prob = prob
        self.logger = logger
        self.replace_subjects = {}

    def update_graph(self, graph):
        subjects_only = get_all_instance_ids(graph)
        amount = int(len(subjects_only) * self.prob)
        sampled_rows = subjects_only.sample(amount)

        for triple in sampled_rows.iterrows():
            s = triple[1]["s"]
            p = triple[1]["p"]
            o = triple[1]["o"]
            target = insert_str(s, ''.join(random.sample(get_invalid_characters(), random.randint(1, 3))),
                                random.randint(-1, len(s)))
            placeholder = f":placeholder-{uuid.uuid4()}"

            try:  # int and float values bug in _is_valid_uri
                valid_uri = rdflib.term._is_valid_uri(o)
                if valid_uri:
                    sparql_update_subject(graph, rdflib.URIRef(s), rdflib.URIRef(p), rdflib.URIRef(o),
                                          rdflib.URIRef(placeholder))
                else:
                    sparql_update_subject(graph, rdflib.URIRef(s), rdflib.URIRef(p), Literal(o),
                                          rdflib.URIRef(placeholder))
            except:
                sparql_update_subject(graph, rdflib.URIRef(s), rdflib.URIRef(p), Literal(o), rdflib.URIRef(placeholder))

            self.replace_subjects[placeholder] = f"{target}"
            self.logger.log_error('corrupt_instance_id', s, s, target, "syntactic")

        return graph

    def post_process(self, file):
        with open(file, 'r') as f:
            filedata = f.read()

        for placeholder, subject in self.replace_subjects.items():
            filedata = filedata.replace(placeholder, subject)

        # Write the file out again
        with open(file, 'w') as f:
            f.write(filedata)


class SemanticSyntacticPropertyNameError(AbstractError):
    def __init__(self, prob, logger):
        super(SemanticSyntacticPropertyNameError, self).__init__()
        self.name = "Semantic Syntactic Property Name Violation"
        self.prob = prob
        self.logger = logger

    def update_graph(self, graph):
        triple_property_only = get_properties(graph)
        amount = int(len(triple_property_only) * self.prob)
        sampled_triples = triple_property_only.sample(n=amount)

        for triple in sampled_triples.iterrows():
            s = triple[1]["s"]
            p = triple[1]["p"]
            o = triple[1]["o"]
            original_ns = get_namespace_from_uri(graph, p)

            if original_ns is not None:
                chars = get_random_characters(length=5)
                prefix, full_ns, target = graph.compute_qname(URIRef(p))
                target = insert_str(target, chars, -1)
                original_ns.__annotations__[target] = URIRef
                full_target = original_ns[target]
                graph.bind(prefix, original_ns, override=True)

                if rdflib.term._is_valid_uri(o):
                    sparql_update_predicate(graph, rdflib.URIRef(s), rdflib.URIRef(p), rdflib.URIRef(o),
                                            rdflib.URIRef(full_target))
                else:
                    sparql_update_predicate(graph, rdflib.URIRef(s), rdflib.URIRef(p), Literal(o),
                                            rdflib.URIRef(full_target))

                self.logger.log_error('corrupt_property_name', s, p, str(full_target), "semantic-syntactic")

        return graph

    def post_process(self, file):
        pass


class SemanticDomainTypeError(AbstractError):
    def __init__(self, prob, logger):
        super(SemanticDomainTypeError, self).__init__()
        self.name = "Semantic Domain Violation"
        self.prob = prob
        self.logger = logger

    def update_graph(self, graph):
        subjects_only = get_subject_only_entities_with_count(graph)
        triple_count = get_triple_count(graph)
        subjects_only["count"] /= triple_count
        subjects_only = subjects_only.sort_values(by=["count"])

        corrupted_pct = 0.0
        while corrupted_pct < self.prob and len(subjects_only) > 0:
            greedy_idx = (np.searchsorted(subjects_only["count"].values, self.prob - corrupted_pct) - 1).clip(0)
            greedy_row = subjects_only.iloc[greedy_idx]
            # cannot add another entity without exceeding threshold
            if greedy_row["count"] + corrupted_pct > self.prob:
                break

            s = greedy_row["s"]
            o = greedy_row["o"]
            corr_o = str(random.choice(dir(SDO)))
            sparql_update_object(graph, rdflib.URIRef(s), RDF.type, rdflib.URIRef(o),
                                 rdflib.URIRef(corr_o))  # random SDO type for now
            self.logger.log_error('corrupt_domain', s, o, corr_o, "semantic")
            corrupted_pct += greedy_row["count"]
            subjects_only = subjects_only.drop(subjects_only.index[greedy_idx])

        return graph

    def post_process(self, file):
        pass


class SemanticRangeTypeError(AbstractError):
    def __init__(self, prob, logger):
        super(SemanticRangeTypeError, self).__init__()
        self.name = "Semantic Range Violation"
        self.prob = prob
        self.logger = logger

    def update_graph(self, graph):
        objects_only = get_object_only_entities_with_count(graph)
        triple_count = get_triple_count(graph)
        objects_only["count"] /= triple_count
        objects_only = objects_only.sort_values(by=["count"])

        corrupted_pct = 0.0
        while corrupted_pct < self.prob and len(objects_only) > 0:
            greedy_idx = (np.searchsorted(objects_only["count"].values, self.prob - corrupted_pct) - 1).clip(0)
            greedy_row = objects_only.iloc[greedy_idx]
            # cannot add another entity without exceeding threshold
            if greedy_row["count"] + corrupted_pct > self.prob:
                break

            s = greedy_row["s"]
            o = greedy_row["o"]
            corr_o = str(random.choice(dir(SDO)))
            sparql_update_object(graph, rdflib.URIRef(s), RDF.type, rdflib.URIRef(o),
                                 rdflib.URIRef(corr_o))  # random SDO type for now
            self.logger.log_error('corrupt_range', s, o, corr_o, "semantic")
            corrupted_pct += greedy_row["count"]
            objects_only = objects_only.drop(objects_only.index[greedy_idx])

        return graph

    def post_process(self, file):
        pass


error_mapping = {
    "semantic": {
        "DomainTypeError": SemanticDomainTypeError,
        "RangeTypeError": SemanticRangeTypeError
    },
    "semantic-syntactic": {
        "InstanceIdentifierError": SemanticSyntacticInstanceIdentifierError,
        "PropertyNameError": SemanticSyntacticPropertyNameError
    },
    "syntactic": {
        "InstanceIdentifierError": SyntacticInstanceIdentifierError
    }
}
