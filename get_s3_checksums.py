#!/usr/bin/env python
"""
Get S3 checksums.

Usage:
    get_s3_checksums.py <S3_PREFIX> [--checksums=<CHECKSUMS>]
    get_s3_checksums.py (-h | --help)

Options:
    -h --help                Show this screen.
    --checksums=<CHECKSUMS>  Comma-separated list of checksums to fetch.
                             [default: md5,sha1,sha256,sha512]
"""

import csv
import hashlib
import sys
import urllib.parse

import boto3
import docopt

from concurrently import concurrently


def list_s3_objects(sess, *, bucket, prefix):
    client = sess.client("s3")
    paginator = client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for s3_obj in page["Contents"]:
            yield {"bucket": bucket, "key": s3_obj["Key"]}


def get_s3_object_checksums(sess, *, bucket, key, checksums):
    hashes = {
        name: hashlib.new(name)
        for name in checksums
    }

    s3_obj = sess.client("s3").get_object(Bucket=bucket, Key=key)

    while chunk := s3_obj["Body"].read(8192):
        for hv in hashes.values():
            hv.update(chunk)

    result = {
        'bucket': bucket,
        'key': key,
        'size': s3_obj["ContentLength"],
        'ETag': s3_obj["ETag"],
        'last_modified': s3_obj["LastModified"].isoformat()
    }

    for name, hv in hashes.items():
        result[f"checksum.{name}"] = hv.hexdigest()

    return result


def main():
    args = docopt.docopt(__doc__)

    checksums = args["--checksums"].split(",")

    for h in checksums:
        if h not in hashlib.algorithms_available:
            sys.exit(f"Unavailable/unrecognised checksum algorithm: {h!r}")

    s3_prefix = args["<S3_PREFIX>"]
    bucket = urllib.parse.urlparse(s3_prefix).netloc
    prefix = urllib.parse.urlparse(s3_prefix).path.lstrip("/")

    out_path = "checksums__" + s3_prefix.replace("s3://", "").replace("/", "_") + ".csv"

    sess = boto3.Session()

    fieldnames = ["bucket", "key", "size", "ETag", "last_modified"] + [
        f"checksum.{name}" for name in checksums
    ]

    with open(out_path, 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for s3_obj in list_s3_objects(sess, bucket=bucket, prefix=prefix):
            writer.writerow(get_s3_object_checksums(sess, **s3_obj, checksums=checksums))

    print(out_path)


if __name__ == "__main__":
    main()
