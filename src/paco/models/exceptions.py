class InvalidPacoFieldType(Exception):
    title = "Invalid Paco field type in YAML"

class InvalidPacoSchema(Exception):
    title = "YAML is not a valid Paco schema"

class InvalidPacoProjectFile(Exception):
    title = "Invalid Paco project YAML file"

class UnusedPacoProjectField(Exception):
    title = "Unused Paco project field in YAML"

class InvalidPacoReference(Exception):
    title = "Invalid Paco reference"

class InvalidCFNMapping(Exception):
    title = "Invalid CloudFormation Mapping from Paco model object"

class InvalidPacoBucket(Exception):
    title = "Invalid Paco Bucket"

class InvalidAWSResourceName(Exception):
    title = "Name is not valid to use as an AWS Resource name"

class TroposphereConversionError(Exception):
    title = "Troposphere Conversion Error"

class InvalidModelObject(Exception):
    title = "Invalide Model Object"