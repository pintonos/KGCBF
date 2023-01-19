# Knowledge Graph Curation Benchmark Framework (KGCBF)

Framework for evaluating correction and completion approaches.

For correction it injects specific semantic and syntactic errors into Knowledge graphs. For completion different links are removed. These changes are recorded and after the approach corrected / completed the KG the evaluation module looks up the changed triples and evaluates their correctness.

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

| name                                  | content                                                                                                            |
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
