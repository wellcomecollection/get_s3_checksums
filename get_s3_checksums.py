#!/usr/bin/env python
"""
Get checksums of objects in Amazon S3.

This script creates a spreadsheet with the checksums of all the objects
within a given S3 prefix.  Prints the name of the finished spreadsheet.

Usage:
    get_s3_checksums.py <S3_PREFIX> [--checksums=<CHECKSUMS>] [--concurrency=<CONCURRENCY>]
    get_s3_checksums.py (-h | --help)

Options:
    -h --help                    Show this screen.
    --checksums=<CHECKSUMS>      Comma-separated list of checksums to fetch.
                                 [default: md5,sha1,sha256,sha512]
    --concurrency=<CONCURRENCY>  Max number of objects to fetch from S3 at once.
                                 [default: 5]
"""

import csv
import hashlib
import secrets
import sys
import urllib.parse

import boto3
import docopt

from concurrently import concurrently


def list_s3_objects(sess, *, bucket, prefix):
    client = sess.client("s3")
    paginator = client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for s3_obj in page.get("Contents", []):
            yield {"bucket": bucket, "key": s3_obj["Key"]}


def get_s3_object_checksums(sess, *, bucket, key, checksums):
    hashes = {name: hashlib.new(name) for name in checksums}

    s3_obj = sess.client("s3").get_object(Bucket=bucket, Key=key)

    while chunk := s3_obj["Body"].read(8192):
        for hv in hashes.values():
            hv.update(chunk)

    result = {
        "bucket": bucket,
        "key": key,
        "size": s3_obj["ContentLength"],
        "ETag": s3_obj["ETag"],
        "VersionId": s3_obj.get("VersionId", ""),
        "last_modified": s3_obj["LastModified"].isoformat(),
    }

    for name, hv in hashes.items():
        result[f"checksum.{name}"] = hv.hexdigest()

    return result


def main():
    args = docopt.docopt(__doc__)

    checksums = args["--checksums"].split(",")
    max_concurrency = int(args["--concurrency"])

    for h in checksums:
        if h not in hashlib.algorithms_available:
            sys.exit(f"Unavailable/unrecognised checksum algorithm: {h!r}")

    s3_prefix = args["<S3_PREFIX>"]
    bucket = urllib.parse.urlparse(s3_prefix).netloc
    prefix = urllib.parse.urlparse(s3_prefix).path.lstrip("/")

    s3_slug = s3_prefix.replace("s3://", "").replace("/", "_")
    random_suffix = secrets.token_hex(3)
    out_path = f"checksums.{s3_slug}.{random_suffix}.csv"

    sess = boto3.Session()

    fieldnames = ["bucket", "key", "size", "ETag", "VersionId", "last_modified"] + [
        f"checksum.{name}" for name in checksums
    ]

    with open(out_path, "w") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for _, output in concurrently(
            lambda s3_obj: get_s3_object_checksums(sess, **s3_obj, checksums=checksums),
            list_s3_objects(sess, bucket=bucket, prefix=prefix),
            max_concurrency=max_concurrency
        ):
            writer.writerow(output)

    print(out_path)


if __name__ == "__main__":
    main()
