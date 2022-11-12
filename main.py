import argparse

from framework.Validators import ValidatrrValidator
from framework.utils import read_config
from framework.error_types import *
from framework.logger import Logger

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, default='input.ttl')
    parser.add_argument('--output', '-o', type=str, default='output.ttl')
    parser.add_argument('--config', '-c', type=str, default='config.yaml')
    args, _ = parser.parse_known_args()
    print(args)

    config = read_config(args.config)
    print(config)

    g = Graph()

    if args.input is not None:
        g = g.parse(args.input)
    print(g.serialize())
    print("---------------------------------------------------------------")

    logger = Logger()
    # g = DomainTypeError(prob=config['DomainTypeError'], logger=logger).update_graph(g)
    g = RangeTypeError(prob=config['RangeTypeError'], logger=logger).update_graph(g)
    # TODO rethink: ex:Georg a ex:Person -> person is also only used as object, sparql finds this tuple
    # g = WrongInstanceError(prob=0.5).update_graph(g)

    # alter graph
    print(g.serialize())
    g.serialize(destination=args.output, format="turtle")

    # save introduced errors
    print(logger)
    logger.save_to_file()

    # validate using validatrr
    v = ValidatrrValidator(logger)
    v.validate_file(args.output)
    v.validate_errors()
