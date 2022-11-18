import argparse
import re
import sys

import boto3
from botocore.exceptions import ClientError

import csv


class ParameterImporter(object):
    def __init__(self):
        self.source_file = None
        self.target_profile = None
        self.target_region = None
        self.target_ssm = None
        self.target_sts = None

    @staticmethod
    def connect_to(profile, region):
        kwargs = {}
        if profile is not None:
            kwargs["profile_name"] = profile
        if region is not None:
            kwargs["region_name"] = region
        return boto3.Session(**kwargs)

    def connect_to_target(self, profile, region):
        self.target_ssm = self.connect_to(profile, region).client("ssm")
        self.target_sts = self.connect_to(profile, region).client("sts")

    def import_params (
        self,
        overwrite,
        keep_going=False,
        key_id=None,
        clear_kms_key=False
    ):
        export_parameters = []

        with open(self.source_file, 'r') as file:
            csv_file = csv.DictReader(file)
            for parameter in csv_file:
                name = parameter["Name"]
                if self.dry_run:
                    sys.stdout.write(f"DRY-RUN: importing {name} \n")
                else:
                    try:
                        if "KeyId" in parameter and key_id is not None:
                            parameter["KeyId"] = key_id
                        if "KeyId" in parameter and clear_kms_key:
                            del parameter["KeyId"]
                        if "KeyId" in parameter:
                            if not parameter["KeyId"]:
                                del parameter["KeyId"]
                        if "LastModifiedDate" in parameter:
                            del parameter["LastModifiedDate"]
                        if "LastModifiedUser" in parameter:
                            del parameter["LastModifiedUser"]
                        if "Version" in parameter:
                            del parameter["Version"]
                        if "Policies" in parameter:
                            if not parameter["Policies"]:
                                # an empty policies list causes an exception
                                del parameter["Policies"]
                        parameter["Overwrite"] = overwrite
                        self.target_ssm.put_parameter(**parameter)
                        sys.stdout.write(f"INFO: import {name} \n")
                    except self.target_ssm.exceptions.ParameterAlreadyExists as e:
                        if not keep_going:
                            sys.stderr.write(
                                f"ERROR: failed to import {name} as it already exists: specify --overwrite or --keep-going\n"
                            )
                            exit(1)
                        else:
                            sys.stderr.write(
                                f"WARN: skipping import {name} already exists\n"
                            )
                    except ClientError as e:
                        msg = e.response["Error"]["Message"]
                        sys.stderr.write(
                            f"ERROR: failed to import {name} , {msg}\n"
                        )
                        if not keep_going:
                            exit(1)

    def main(self):
        parser = argparse.ArgumentParser(description="import parameter store ")
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--overwrite",
            "-f",
            dest="overwrite",
            action="store_true",
            help="existing values",
        )
        group.add_argument(
            "--keep-going",
            "-k",
            dest="keep_going",
            action="store_true",
            help="as much as possible after an error",
        )
        parser.add_argument(
            "--dry-run",
            "-N",
            dest="dry_run",
            action="store_true",
            help="only show what is to be import",
        )
        parser.add_argument(
            "--region",
            dest="target_region",
            help="to import the parameters to ",
            metavar="AWS::Region",
        )
        parser.add_argument(
            "--profile",
            dest="target_profile",
            help="to import the parameters to",
            metavar="NAME",
        )
        parser.add_argument(
            "--file",
            dest="source_file",
            help="The file path to export to",
        )
        options = parser.parse_args()

        try:
            self.connect_to_target(options.target_profile, options.target_region)
            self.source_file = options.source_file
            self.dry_run = options.dry_run
            self.import_params(
                options.overwrite,
                options.keep_going
            )
        except ClientError as e:
            sys.stderr.write("ERROR: {}\n".format(e))
            sys.exit(1)


def main():
    cp = ParameterImporter()
    cp.main()

if __name__ == "__main__":
    main()