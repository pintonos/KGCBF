import uuid
from utils.sparql_utils import *
from utils.corruption_utils import *
from utils.rdf_utils import *


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


class LocalSyntacticTypeError(AbstractError):
    def __init__(self, prob, logger):
        super(LocalSyntacticTypeError, self).__init__()
        self.name = "Local Syntactic Type Violation"
        self.prob = prob
        self.logger = logger
        self.replace_objects = {}

    def update_graph(self, graph):
        instances = get_all_instance_declarations(graph)
        amount = int(len(instances) * self.prob)
        sampled_rows = instances.sample(amount)

        for triple in sampled_rows.iterrows():
            s = triple[1]["s"]
            p = triple[1]["p"]
            o = triple[1]["o"]
            original_ns = get_namespace_from_uri(graph, o)

            if original_ns is not None:
                chars = get_random_characters(length=5)
                prefix, full_ns, target = graph.compute_qname(URIRef(o))
                target = insert_str(target, chars, -1)
                original_ns.__annotations__[target] = URIRef
                full_target = original_ns[target]
                graph.bind(prefix, original_ns, override=True)
                update_object(graph, s, p, o, full_target)

                org_triple = {"s": s, "p": p, "o": o}
                corr_triple = {"s": s, "p": p, "o": str(full_target)}
                self.logger.log_error('corrupt_type', "local-syntactic", org_triple, corr_triple)

        return graph

    def post_process(self, file):
        pass



class LocalSyntacticInstanceIdentifierError(AbstractError):
    def __init__(self, prob, logger):
        super(LocalSyntacticInstanceIdentifierError, self).__init__()
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
                update_subject(graph, s, p, o, target)

                org_triple = {"s": s, "p": p, "o": o}
                corr_triple = {"s": target, "p": p, "o": o}
                self.logger.log_error('corrupt_instance_id', "local-syntactic", org_triple, corr_triple)

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
            update_subject(graph, s, p, o, placeholder)
            self.replace_subjects[placeholder] = target

            org_triple = {"s": s, "p": p, "o": o}
            corr_triple = {"s": target, "p": p, "o": o}
            self.logger.log_error('corrupt_instance_id', "syntactic", org_triple, corr_triple)

        return graph

    def post_process(self, file):
        with open(file, 'r') as f:
            file_data = f.read()

        for placeholder, subject in self.replace_subjects.items():
            file_data = file_data.replace(placeholder, subject)

        # Write the file out again
        with open(file, 'w') as f:
            f.write(file_data)


class SyntacticTypeError(AbstractError):
    def __init__(self, prob, logger):
        super(SyntacticTypeError, self).__init__()
        self.name = "Syntactic Type Violation"
        self.prob = prob
        self.logger = logger
        self.replace_objects = {}

    def update_graph(self, graph):
        instances = get_all_instance_declarations(graph)
        amount = int(len(instances) * self.prob)
        sampled_rows = instances.sample(amount)

        for triple in sampled_rows.iterrows():
            s = triple[1]["s"]
            p = triple[1]["p"]
            o = triple[1]["o"]
            target = insert_str(o, ''.join(random.sample(get_invalid_characters(), random.randint(1, 3))),
                                random.randint(-1, len(o)))
            placeholder = f":placeholder-{uuid.uuid4()}"
            update_object(graph, s, p, o, placeholder)
            self.replace_objects[placeholder] = target

            org_triple = {"s": s, "p": p, "o": o}
            corr_triple = {"s": s, "p": p, "o": target}
            self.logger.log_error('corrupt_type', "syntactic", org_triple, corr_triple)

        return graph

    def post_process(self, file):
        with open(file, 'r') as f:
            file_data = f.read()

        for placeholder, object in self.replace_objects.items():
            file_data = file_data.replace(placeholder, object)

        # Write the file out again
        with open(file, 'w') as f:
            f.write(file_data)


class SyntacticPropertyError(AbstractError):
    def __init__(self, prob, logger):
        super(SyntacticPropertyError, self).__init__()
        self.name = "Syntactic Property Value Violation"
        self.prob = prob
        self.logger = logger
        self.replace_property = {}

    def update_graph(self, graph):
        instances = get_all_instance_ids(graph)
        amount = int(len(instances) * self.prob)
        sampled_rows = instances.sample(amount)

        for triple in sampled_rows.iterrows():
            s = triple[1]["s"]
            p = triple[1]["p"]
            o = triple[1]["o"]
            target = insert_str(p, ''.join(random.sample(get_invalid_characters(), random.randint(1, 3))),
                                random.randint(-1, len(p)))
            placeholder = f"placeholder-{uuid.uuid4()}"
            update_predicate(graph, s, p, o, placeholder)
            self.replace_property[placeholder] = f"{target}"

            org_triple = {"s": s, "p": p, "o": o}
            corr_triple = {"s": s, "p": target, "o": o}
            self.logger.log_error('corrupt_property', "syntactic", org_triple, corr_triple)

        return graph

    def post_process(self, file):
        with open(file, 'r') as f:
            file_data = f.read()

        for placeholder, property in self.replace_property.items():
            file_data = file_data.replace(placeholder, property)

        # Write the file out again
        with open(file, 'w') as f:
            f.write(file_data)


class SyntacticPropertyAssertionError(AbstractError):
    def __init__(self, prob, logger):
        super(SyntacticPropertyAssertionError, self).__init__()
        self.name = "Syntactic Property Assertion Violation"
        self.prob = prob
        self.logger = logger
        self.replace_objects = {}

    def update_graph(self, graph):
        assertions = get_properties(graph)
        amount = int(len(assertions) * self.prob)
        sampled_rows = assertions.sample(amount)

        for triple in sampled_rows.iterrows():
            s = triple[1]["s"]
            p = triple[1]["p"]
            o = triple[1]["o"]
            target = insert_str(o, ''.join(random.sample(get_invalid_characters(), random.randint(1, 3))),
                                random.randint(-1, len(o)))
            placeholder = f":placeholder-{uuid.uuid4()}"
            update_object(graph, s, p, o, placeholder)
            self.replace_objects[placeholder] = target
            org_triple = {"s": s, "p": p, "o": o}
            corr_triple = {"s": s, "p": p, "o": str(target)}
            self.logger.log_error('corrupt_assertion', "syntactic", org_triple, corr_triple)

        return graph

    def post_process(self, file):
        with open(file, 'r') as f:
            file_data = f.read()

        for placeholder, object in self.replace_objects.items():
            file_data = file_data.replace(placeholder, object)

        # Write the file out again
        with open(file, 'w') as f:
            f.write(file_data)


class LocalSyntacticPropertyNameError(AbstractError):
    def __init__(self, prob, logger):
        super(LocalSyntacticPropertyNameError, self).__init__()
        self.name = "Local Syntactic Property Value Violation"
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
                update_predicate(graph, s, p, o, full_target)

                org_triple = {"s": s, "p": p, "o": o}
                corr_triple = {"s": s, "p": str(full_target), "o": o}
                self.logger.log_error('corrupt_property', "local-syntactic", org_triple, corr_triple)

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
            update_object(graph, s, RDF.type, o, corr_o)  # random SDO type for now

            org_triple = {"s": s, "p": str(RDF.type), "o": o}
            corr_triple = {"s": s, "p": str(RDF.type), "o": corr_o}
            self.logger.log_error('corrupt_domain', "semantic", org_triple, corr_triple)

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
            update_object(graph, s, RDF.type, o, corr_o)  # random SDO type for now

            org_triple = {"s": s, "p": str(RDF.type), "o": o}
            corr_triple = {"s": s, "p": str(RDF.type), "o": corr_o}
            self.logger.log_error('corrupt_range', "semantic", org_triple, corr_triple)

            corrupted_pct += greedy_row["count"]
            objects_only = objects_only.drop(objects_only.index[greedy_idx])

        return graph

    def post_process(self, file):
        pass


class SemanticInstanceAssertionError(AbstractError):
    def __init__(self, prob, logger):
        super(SemanticInstanceAssertionError, self).__init__()
        self.name = "Semantic Instance Assertion Error"
        self.prob = prob
        self.logger = logger

    def update_graph(self, graph):
        subjects_only = get_all_instance_declarations(graph)
        amount = int(len(subjects_only) * self.prob)
        sampled_rows = subjects_only.sample(amount)

        for triple in sampled_rows.iterrows():
            s = triple[1]["s"]
            p = triple[1]["p"]
            o = triple[1]["o"]
            corr_o = str(random.choice(dir(SDO)))
            update_object(graph, s, RDF.type, o, corr_o)  # random SDO type for now

            org_triple = {"s": s, "p": str(RDF.type), "o": o}
            corr_triple = {"s": s, "p": str(RDF.type), "o": corr_o}

            org_triple = {"s": s, "p": p, "o": o}
            corr_triple = {"s": s, "p": p, "o": corr_o}
            self.logger.log_error('corrupt_instance_assertion', "semantic", org_triple, corr_triple)

        return graph

    def post_process(self, file):
        pass


class SemanticPropertyAssertionError(AbstractError):
    def __init__(self, prob, logger):
        super(SemanticPropertyAssertionError, self).__init__()
        self.name = "Semantic Property Assertion Error"
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
            corr_p = str(random.choice(dir(SDO))) # TODO only lowercase refs?
            update_predicate(graph, s, p, o, corr_p) # random SDO type for now

            org_triple = {"s": s, "p": p, "o": o}
            corr_triple = {"s": s, "p": corr_p, "o": o}
            self.logger.log_error('corrupt_property_assertion', "semantic", org_triple, corr_triple)

        return graph

    def post_process(self, file):
        pass


error_mapping = {
    "semantic": {
        "DomainTypeError": SemanticDomainTypeError,
        "RangeTypeError": SemanticRangeTypeError,
        "InstanceAssertionError": SemanticInstanceAssertionError,
        "PropertyAssertionError": SemanticPropertyAssertionError
    },
    "local-syntactic": {
        "InstanceIdentifierError": LocalSyntacticInstanceIdentifierError,
        "TypeError": LocalSyntacticTypeError,
        "PropertyError": LocalSyntacticPropertyNameError
    },
    "syntactic": {
        "InstanceIdentifierError": SyntacticInstanceIdentifierError,
        "TypeError": SyntacticTypeError,
        "PropertyNameError": SyntacticPropertyError,
        "PropertyAssertionError": SyntacticPropertyAssertionError
    }
}
