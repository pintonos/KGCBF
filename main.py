import argparse
import numpy as np
from rdflib import Graph

from framework.utils import construct_error_example_graph, random_replace_character
from framework.queries import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, default='http://www.w3.org/People/Berners-Lee/card')
    parser.add_argument('--output', '-o', type=str, default='output.ttl')
    args, _ = parser.parse_known_args()
    print(args)

    g = Graph()
    
    #if args.input is not None:
    #    g = g.parse(args.input)
    #else:
    g = construct_error_example_graph()

    g.update(
        """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX error_foaf: <http://xmlns.com/foaf/0.1/ERROR/>
        PREFIX ex: <http://example.org/people/>
        DELETE {
            ex:Linda a ?o .
        }
        INSERT { 
            ex:Linda1 a ?o . 
        }
        WHERE {
            ex:Linda a ?o .
        }
        """
    )

    print(g.serialize())
    g.serialize(destination=args.output, format="turtle")

    # alter serialized version with syntax errors
    '''with open(args.output, "r+") as f:
        rdf_str = f.read()
        rdf_str = random_replace_character(rdf_str, ";", prob=0.5)
        rdf_str = random_replace_character(rdf_str, ".", prob=0.5)
        f.write(rdf_str)'''

    # check compabitiblity
    g.parse(args.output)