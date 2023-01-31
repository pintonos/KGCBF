import argparse
import copy

from corruption.error_types import *
from corruption.logger import Logger
from evaluation.validation import ValidationMethodsDict
from utils.rdf_utils import extract_subgraph, read_config, get_shacl_from_ontology


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, default='datasets/input.ttl')
    parser.add_argument('--output', '-o', type=str, default='data/output.ttl')
    parser.add_argument('--ontology', '-on', type=str)
    parser.add_argument('--config', '-c', type=str, default='config.yaml')
    parser.add_argument('--validation', '-v', type=str)
    parser.add_argument('--shacl', '-s', action='store_true')
    parser.add_argument('--report', '-r', type=str, default='data/report.yaml')
    parser.add_argument('--subgraph', '-sub', type=float, default=1.0)
    parser.add_argument('--multi', '-m', action='store_true')
    args, _ = parser.parse_known_args()
    print(args)

    config = read_config(args.config)
    print(yaml.dump(config, allow_unicode=True, default_flow_style=False), "\n\n")

    g = Graph()

    if args.input is not None:
        g = g.parse(args.input)
        if 1.0 > args.subgraph > 0.0:
            g = extract_subgraph(g, size=args.subgraph, levels=1)
    logger = Logger()

    error_instantiations = {cat: {} for cat in config["errors"]}

    # switch to multi-error per triple if config prob. sum > 1.0
    if sum([prob for error in config["errors"].values() for prob in error.values()]) > 1.0:
        print("Config error probabilites > 1.0 >>>> multi-error per triple activated!", "\n\n")
        args.multi = True

    # alter graph
    original_graph, corrupted_triples = None, None
    if not args.multi:
        original_graph = copy.deepcopy(g)
        corrupted_triples = Graph()
    for cat in config["errors"]:
        for error in config["errors"][cat]:
            if cat in error_mapping and error in error_mapping[cat]:
                prob = config["errors"][cat][error]
                print(f"Adding error type {error} in category {cat} with prob {prob}.")
                error_instantiations[cat][error] = error_mapping[cat][error](prob=prob, logger=logger)
                if args.multi or cat == 'syntactic':
                    g = error_instantiations[cat][error].update_graph(g)
                else:
                    # remove corrupted triples from graph to prevent multiple corruptions per triple
                    g = error_instantiations[cat][error].update_graph(g)
                    corrupted_triples += g - original_graph
                    g -= corrupted_triples
            else:
                print(f"Skipping unknown error type: {cat} {error}.")

    if not args.multi:
        g = g + corrupted_triples

    # add ontology and/or shacl shapes graph
    if args.shacl and not args.ontology:
        print("!!!Closed world assumption requires a shapes graph passed via --ontology or -on!!!")
        print("Skipping CWA.")
    elif args.shacl:
        get_shacl_from_ontology(args.ontology)
        shacl_graph = Graph()
        shacl_graph.parse("ontology_shacl.ttl")
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
        if args.validation not in ValidationMethodsDict:
            print(f"Validation method '{args.validation}' does not exist.")
        else:
            v = ValidationMethodsDict[args.validation](args.output, logger)
            kgcbf_report = v.evaluate_errors(args.report)
            print(kgcbf_report)
