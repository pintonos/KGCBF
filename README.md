# Knowledge Graph Curation Benchmark Framework (KGCBF)

Framework for evaluating correction and completion approaches.

For correction it injects specific semantic and syntactic errors into Knowledge graphs. For completion different links are removed. These changes are recorded and after the approach corrected / completed the KG the evaluation module looks up the changed triples and evaluates their correctness.

## Evaluation Module
The evaluation module feeds the corrupted graph into a cleaning/evaluation approach. 
The current setup requires the evaluation approach to take a `.ttl` file as an input, 
and requires it to provide an output report in the form of a graph or text file. 

### Evaluation Module Output
TODO

### Benchmarking Your Own Approach
To benchmark your own (or someone else's!) validation approach, follow the following steps.

#### Create an Approach Dictionary
First, create an approach dictionary in `evaluation/validators/dictionaries`. See a sample dictionary below.
```yaml
type: "regex" # or graph
total_errors:
  pattern: "Error[1-9]+" # this pattern should match exactly once per error 
corrupt_instance_id: # here, you can pick a type of error which the approach can detect
  patterns: # Errors can have multiple patterns
    - "Error[1-9]+.*\n.*$corrupt.subject$" # Use the placeholders to template your queries
    - "Error.*\n.*$original.object$" # different pattern
corrupt_property:
  patterns:
    - "Error[1-9]+.*\n.*$corrupt.predicate$" # use the patterns array anyway, even for 1 pattern
```
Your dictionary should specify whether the output (type) of your validation approach is a graph (graph) or a text file (regex). 
The total_errors pattern should match once to each error, to allow KGCBF to count the number of total detected errors. 
Then, for each error type as specified in the config, you can provide one or multiple patterns (SPARQL for graph, regex for regex) 
which match to the specific error. You can use the placeholders `$original.subject$`, `$original.predicate$`, `$original.object$`, 
`$corrupted.subject$`, `$corrupted.predicate$`, `$corrupted.object$`, which will be replaced with the corresponding 
entries of the original (before corruption) or corrupted (after corruption) triple for each introduced corruption.

#### Create a Validation Class
In `evaluation/validators/`, create a new class which extends `AbstractValidator`. 
Provide the three class variables `name`, `approach_dictionary` and `output_file`. The name is simply the display name 
of your validation approach. The approach_dictionary is the file path from the main directory (main.py) to the dictionary 
you created in the previous step. The output_file is the name of the file which your validation approach creates (again, relative 
to the main.py directory).

Override the methods `validate_file(self)` and `evaluate_errors(self)`. Usually, the code of `evaluate_errors(self)` can just be copied. 
In `validate_file(self)`, you will have to bootstrap your validation tool so that it generates the output_file 
from the `input_graph` provided in the constructor. See the existing validators for an idea of how to do that (e.g., you can call 
a CLI tool or start a Docker container, or implement a python library if one is available for your tool).

#### Add Your Approach To The Dictionary
Finally, you must add your new created class to `evaluation/validation.py`, by resolving an arbitrary 
string name to your class in `ValidationMethodsDict`. After doing this, you can call the CLI tool with `-v [your tool name]`
 and the KGCBF report will be generated.

# Links
- https://www.wikidata.org/wiki/Special:EntityData/Q42.ttl
- http://dbpedia.org/resource/Richard_Nixon
