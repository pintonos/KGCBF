import argparse

from rdflib import Graph

from framework.validators import ValidatrrValidator
from framework.utils import read_config, get_shacl_from_ontology
from framework.error_types import *
from framework.logger import Logger

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, default='datasets/input.ttl')
    parser.add_argument('--output', '-o', type=str, default='data/output.ttl')
    parser.add_argument('--ontology', '-on', type=str)
    parser.add_argument('--config', '-c', type=str, default='config.yaml')
    parser.add_argument('--validation', '-v', type=str)
    parser.add_argument('--shacl', '-s', action='store_true')
    args, _ = parser.parse_known_args()
    print(args)

    config = read_config(args.config)
    print(config, "\n\n")

    g = Graph()

    if args.input is not None:
        g = g.parse(args.input)
    print(g.serialize())
    print("---------------------------------------------------------------")

    logger = Logger()

    # alter graph
    g = DomainTypeError(prob=config['DomainTypeError'], logger=logger).update_graph(g)
    g = RangeTypeError(prob=config['RangeTypeError'], logger=logger).update_graph(g)
    # g = WrongInstanceError(prob=0.5).update_graph(g)

    # add ontology and/or shacl shapes graph
    if args.shacl and not args.ontology:
        print("!!!Closed world assumption requires a shapes graph passed via --ontology or -on!!!")
        print("Skipping CWA.")
    elif args.shacl:
        get_shacl_from_ontology(args.ontology)
        shacl_graph = Graph()
        shacl_graph.parse("data/ontology_shacl.ttl")
        g = g + shacl_graph
    # add shapes graph to output graph
    elif args.ontology:
        ontology_graph = Graph()
        ontology_graph.parse(args.ontology)
        g = g + ontology_graph

    g.serialize(destination=args.output, format="turtle")

    # save introduced errors
    logger.save_to_file()

    if args.validation is not None:
        # choose validator class here
        v = None
        if args.validation == "validatrr":
            # validate using validatrr
            v = ValidatrrValidator(logger)
        # validate over chosen validator class
        if v:
            v.validate_file(args.output)
            v.validate_errors()
        else:
            print(f"Validation method '{args.validation}' does not exist.")
