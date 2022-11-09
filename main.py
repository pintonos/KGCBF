import argparse
import numpy as np
from rdflib import Graph

from framework.utils import construct_error_example_graph, random_replace_character, construct_example_graph, read_config
#from framework.queries import *
from framework.error_types import *
from framework.logger import Logger


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, default='http://dbpedia.org/resource/Richard_Nixon')
    parser.add_argument('--output', '-o', type=str, default='output.ttl')
    parser.add_argument('--config', '-c', type=str, default='config.yaml')
    args, _ = parser.parse_known_args()
    print(args)

    config = read_config(args.config)
    print(config)

    g = Graph()
    
    #if args.input is not None:
    #    g = g.parse(args.input)
    #else:
    g = construct_example_graph()
    print(g.serialize())
    print("---------------------------------------------------------------")
    
    logger = Logger()
    g = DomainTypeError(prob=config['DomainTypeError'], logger=logger).update_graph(g)    
    #g = RangeTypeError(prob=1.0, logger=logger).update_graph(g) # TODO rethink: ex:Georg a ex:Person -> person is also only used as object, sparql finds this tuple
    #g = WrongInstanceError(prob=0.5).update_graph(g)

    print(g.serialize())
    g.serialize(destination=args.output, format="turtle")

    print(logger)
    logger.save_to_file()

    # alter serialized version with syntax errors
    '''with open(args.output, "r+") as f:
        rdf_str = f.read()
        rdf_str = random_replace_character(rdf_str, ";", prob=0.5)
        rdf_str = random_replace_character(rdf_str, ".", prob=0.5)
        f.write(rdf_str)'''

    # check compabitiblity
    g.parse(args.output)