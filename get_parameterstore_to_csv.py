import argparse
import re
import sys

import boto3
from botocore.exceptions import ClientError

import csv


class ParameterExporter(object):
    def __init__(self):
        self.target_file = None
        self.source_profile = None
        self.source_region = None
        self.source_ssm = None
        self.source_sts = None

    @staticmethod
    def connect_to(profile, region):
        kwargs = {}
        if profile is not None:
            kwargs["profile_name"] = profile
        if region is not None:
            kwargs["region_name"] = region
        return boto3.Session(**kwargs)

    def connect_to_source(self, profile, region):
        self.source_ssm = self.connect_to(profile, region).client("ssm")
        self.source_sts = self.connect_to(profile, region).client("sts")

    def load_source_parameters(self, arg, recursive, one_level):
        result = {}
        paginator = self.source_ssm.get_paginator("describe_parameters")
        kwargs = {}
        if recursive or one_level:
            option = "Recursive" if recursive else "OneLevel"
            kwargs["ParameterFilters"] = [
                {"Key": "Path", "Option": option, "Values": [arg]}
            ]
        else:
            kwargs["ParameterFilters"] = [
                {"Key": "Name", "Option": "Equals", "Values": [arg]}
            ]

        for page in paginator.paginate(**kwargs):
            for parameter in page["Parameters"]:
                result[parameter["Name"]] = parameter

        if len(result) == 0:
            sys.stderr.write("ERROR: {} not found.\n".format(arg))
            sys.exit(1)
        return result

    def export(
        self,
        args,
        recursive,
        one_level,
        with_decryption
    ):
        export_parameters = []

        with open(self.target_file, 'w', newline='') as file:
            fieldnames = ['Name', 'Type','KeyId','LastModifiedDate','LastModifiedUser','Description','Value','AllowedPattern','Tier','Version','Labels','Policies','DataType']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for arg in args:
                parameters = self.load_source_parameters(arg, recursive, one_level)
                for name in parameters:
                    value = self.source_ssm.get_parameter(Name=name, WithDecryption=with_decryption)
                    parameter = parameters[name]
                    parameter["Value"] = value["Parameter"]["Value"]

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

                    writer.writerow(parameter)

    def main(self):
        parser = argparse.ArgumentParser(description="copy parameter store ")
        parser.add_argument(
            "--one-level",
            "-1",
            dest="one_level",
            action="store_true",
            help="one-level copy",
        )
        parser.add_argument(
            "--recursive",
            "-r",
            dest="recursive",
            action="store_true",
            help="recursive copy",
        )
        parser.add_argument(
            "--source-region",
            dest="source_region",
            help="to get the parameters from ",
            metavar="AWS::Region",
        )
        parser.add_argument(
            "--with-decryption",
            "-d",
            dest="with_decryption",
            help="With Decryption",
            metavar="With Decryption",
            default=True, type=bool
        )
        parser.add_argument(
            "--source-profile",
            dest="source_profile",
            help="to obtain the parameters from",
            metavar="NAME",
        )
        parser.add_argument(
            "--file",
            dest="target_file",
            help="The file path to export to",
        )
        parser.add_argument(
            "parameters", metavar="PARAMETER", type=str, nargs="+", help="source path"
        )
        options = parser.parse_args()

        try:
            self.connect_to_source(options.source_profile, options.source_region)
            self.target_file = options.target_file
            self.export(
                options.parameters,
                options.recursive,
                options.one_level,
                options.with_decryption
            )
        except ClientError as e:
            sys.stderr.write("ERROR: {}\n".format(e))
            sys.exit(1)


def main():
    cp = ParameterExporter()
    cp.main()

if __name__ == "__main__":
    main()