import argparse

from framework.error_types import *
from framework.logger import Logger
from framework.validators import ValidatrrValidator

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
    logger = Logger()

    error_instantiations = {cat: {} for cat in config["errors"]}

    # alter graph
    for cat in config["errors"]:
        for error in config["errors"][cat]:
            if cat in error_mapping and error in error_mapping[cat]:
                prob = config["errors"][cat][error]
                print(f"Adding error type {error} in category {cat} with prob {prob}.")
                error_instantiations[cat][error] = error_mapping[cat][error](prob=prob, logger=logger)
                g = error_instantiations[cat][error].update_graph(g)
            else:
                print(f"Skipping unknown error type: {cat} {error}.")

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

    # post-processing (for syntactic errors)
    for cat in error_instantiations:
        for error in error_instantiations[cat]:
            error_instantiations[cat][error].post_process(args.output)

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
