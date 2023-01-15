from evaluation.validators.RdfDoctorValidator import RdfDoctorValidator
from evaluation.validators.ValidatrrValidator import ValidatrrValidator

# After creating a new validator, you must add it here so that it can be used via the CLI.
ValidationMethodsDict = {
    "validatrr": ValidatrrValidator,
    "rdfdoctor": RdfDoctorValidator
}