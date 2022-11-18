# Exporting Existing Configurations

Export the parameters from an AWS account:


```
usage: get_parameterstore_to_csv.py [-h] [--one-level] [--recursive] [--source-region AWS::Region] [--with-decryption With Decryption] [--source-profile NAME]
                                    [--file TARGET_FILE]
                                    PARAMETER [PARAMETER ...]

copy parameter store

positional arguments:
  PARAMETER             source path

options:
  -h, --help            show this help message and exit
  --one-level, -1       one-level copy
  --recursive, -r       recursive copy
  --source-region AWS::Region
                        to get the parameters from
  --with-decryption With Decryption, -d With Decryption
                        With Decryption
  --source-profile NAME
                        to obtain the parameters from
  --file TARGET_FILE    The file path to export to
  
```
  
# Importing Existing CVS to Parameter Store

Import the parameters in an AWS account:


```
usage: set_parameterstore_from_csv.py [-h] [--overwrite | --keep-going] [--dry-run] [--region AWS::Region] [--profile NAME] [--file SOURCE_FILE]

import parameter store

options:
  -h, --help            show this help message and exit
  --overwrite, -f       existing values
  --keep-going, -k      as much as possible after an error
  --dry-run, -N         only show what is to be import
  --region AWS::Region  to import the parameters to
  --profile NAME        to import the parameters to
  --file SOURCE_FILE    The file path to import from
```

