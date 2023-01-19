# Knowledge Graph Curation Benchmark Framework (KGCBF)

The Knowledge Graph Curation Benchmark Framework (KGCBF) is a framework for evaluating error detection- and correction approaches in knowledge graphs.

It is split into a corruption module and an evaluation module, which are accessed using a command line interface.  

To run the benchmark, install dependencies via the provided `Pipfile` and run the `main.py` script. The possible parameters are listed below.  
**Note that the pre-defined validation approaches are subject to additional dependencies. Refer to the Section "Evaluation Module" for more information.**

| Parameter    | Description                                                                                                          |
|--------------|----------------------------------------------------------------------------------------------------------------------|
| --input      | Path to the input knowledge graph (.ttl). Defaults to `datasets/input.ttl`                                           |
| --output     | Path to the corrupted knowledge graph output (.ttl). Defaults to `data/output.ttl`                                   |
| --ontology   | Path to an auxiliary knowledge graph containing ontology or shape triples (.ttl) This graph remains uncorrupted      |
| --config     | Path to the config file (.yaml). Defaults to `config.yaml`.                                                          |
| --validation | Validation approach                                                                                                  |
| --shacl      | If --shacl is set, SHACL shapes are automatically inferred for domain and range violations based on the input graph. |
| --report     | Path to the final evaluation report (.yaml). Defaults to `data/report.yaml`.                                         |
| --subgraph   | Defines the size of the sampled subgraph from the input (0-1). Defaults to 0.5.                                      |
| --multi      | If set, allows multiple errors to occur on a single triple. If not set, only one error is allowed per triple.        |


## Corruption Module 
The corruption module is responsible for generating a knowledge graph for benchmarking by introducing specific corruptions into an 
input knowledge graph which is presumed to be uncorrupted. The input and output graphs are both in the Turtle format, and are provided 
via the `--input` and `--output` parameters. The corruption module is configured via a YAML file, which is provided via the `--config` parameter.
A sample configuration file is shown below.

```yaml
errors:
  semantic:
    DomainTypeError: 0.1
    RangeTypeError: 0.1
    InstanceAssertionError: 0.1
    PropertyAssertionError: 0.1
  local-syntactic:
    InstanceIdentifierError: 0.1
    PropertyNameError: 0.1
    TypeError: 0.1
  syntactic:
    InstanceIdentifierError: 0.2
    TypeError: 0.1
    PropertyNameError: 0.1
    PropertyAssertionError: 0.1
```

We differentiate between three different error categories: semantic, local-syntactic, and syntactic.  
**Semantic** errors are errors related to the semantics of the triples, but the triples themselves are syntactically correct. This category includes:
- `DomainTypeError`: The domain of a property is violated.
- `RangeTypeError`: The range of a property is violated.
- `InstanceAssertionError`: An instance is falsely asserted to be a member of a class (rdf:type relation).
- `PropertyAssertionError`: The property assertion of a triple is semantically incorrect.

We introduce these errors by replacing the object of a triple with a random object from the SDO ontology. In the case of 
domain and range violations, we alter the definition of an instance to induce a violation of the domain or range of a property.
In these cases, we try to approximate the desired error quantity by calculating how many triples would be affected by the change.

**Local-syntactic** errors are errors in the presumed syntax of the knowledge graph. For example, if all instances in a knowledge graph 
are named using the CamelCase convention, then an instance named using the snake_case convention is a local-syntactic error. This category includes:
- `InstanceIdentifierError`: The identifier of an instance does not conform to the expected syntax.
- `PropertyNameError`: The name of a property does not conform to the expected syntax.
- `TypeError`: The type of a literal does not conform to the expected syntax.

We introduce these errors by adding random characters to the identifier of an instance, property, or type definition. 
We ensure that the altered triples still conform to the Turtle syntax.

**Syntactic** errors are errors in the syntax of the knowledge graph. Specifically, we focus on errors in the RDF syntax. Hence, 
we only alter the syntax of subjects, predicates, and objects, but not the syntax of the Turtle declarations. This category includes:
- `InstanceIdentifierError`: The identifier of an instance does not conform to the Turtle syntax.
- `TypeError`: The type of a literal does not conform to the Turtle syntax.
- `PropertyNameError`: The name of a property does not conform to the Turtle syntax.
- `PropertyAssertionError`: The object of a property assertion triple is syntactically incorrect.

We introduce these errors by adding random characters to the identifier of an instance, property, or type definition, where 
the added characters are illegal in the RDF syntax.

### Additional Corruption Module Features
The corruption module also supports the following additional features:

**SHACL Shapes**: The corruption module can automatically infer SHACL shapes for domain and range violations based on the input graph.
This feature is enabled by setting the `--shacl` parameter. Shapes are inferred based on rdfs:domain and rdfs:range definitions. 
The inferred shapes are written to the output graph. This may be useful for evaluating approaches that use SHACL shapes for validation.

**Ontology**: The corruption module can be provided with an auxiliary knowledge graph containing ontology or shape triples.
This graph is provided via the `--ontology` parameter. The corruption module will not corrupt triples in this graph, but 
add this graph to the corrupted output graph in its original form. This allows users to guarantee that the TBox of the corrupted
graph is unaffected and can be used to reason over the ABox.

**Subgraph**: The corruption module can be configured to only corrupt a subgraph of the input graph. This is useful if the
input graph is too large to be corrupted in a reasonable amount of time. The size of the subgraph is defined via the `--subgraph` parameter.

**Multiple Errors**: The corruption module can be configured to allow multiple errors to occur on a single triple. Our 
assumption is that it is generally undesirable to introduce multiple corruptions on a single triple, as the subsequent 
evaluation of the error detection- and correction approaches may be quite difficult. However, some errors are not likely to 
affect one another. In cases where the total number of introduced errors thus exceeds the number of triples in the input graph,
the corruption module will allow multiple errors to occur on a single triple. This behavior can be enabled via the `--multi` parameter.

## Evaluation Module
The evaluation module feeds the corrupted graph into a cleaning/evaluation approach. 
The current setup requires the evaluation approach to take a `.ttl` file as an input, 
and requires it to provide an output report in the form of a graph or text file. 

The evaluation approach is chosen via the `-v` or `--validation` flag of the CLI tool. By default, the available approaches 
are `validatrr` and `rdfdoctor`. However, they both have some external requirements. `rdfdoctor` requires java to be 
installed on the machine, so tha the file `bin/RDFDoctor.jar` can be installed. The `validatrr` approach uses a dockerized 
container approach, which requires the `validatrr` image to be available with the tag `n3unit` for execution via CLI. 
To accomplish this, you can build the validatrr image from [their GitHub Repository](https://github.com/IDLabResearch/validatrr).

### Evaluation Module Output
By default, the tool places the final report at `data/report.yaml`. You can override this location with the `-r` or `--report` flag.
The output is a .yaml file which contains an evaluation of the (mis)match between generated corruptions and the output of the validation approach.

The report contains the following meta-information:  

| Name                                  | Content                                                                                                            |
|---------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| _validator                            | The name of the validation approach.                                                                               |
| _validator_errors                     | How many errors the validation approach has detected.                                                              |
| _explained_errors                     | How many of the _validator_errors can be explained by our introduced corruptions.                                  |
| _recall                               | The true recall of our corruptions (how many corruptions produce at least one matching error).                     |
| _avg_errors_per_introduced_corruption | How many validation errors one of our corruptions generates on average.                                            |
| _estimated_unexplained_corruptions    | Based on _avg_errors_per_introduced_corruptions, how many "corruptions" are detected which we have not introduced. |
| _estimated_precision                  | Using _estimated_unexplained_corruptions, estimate a "precision" of corruption detection.                          |
| _estimated_f1                         | Using _recall and _estimated_precision, estimate the F1 score                                                      |

Further, we split introduced errors based on categories (e.g., semantic or syntactic), and report the total number of introduced and detected 
errors for each category. This helps in distinguishing which category of errors a given tool can detect (e.g., validatrr detects semantic errors, while rdfdoctor 
detects syntactic ones).

Finally, in the `errors_detected` and `errors_not_detected` arrays, we provide a full list of the detected and missed errors. Each error 
contains the original as well as the corrupted triple (subject, predicate and object).

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