# get_s3_checksums

This is a script for getting checksums of objects in Amazon S3.
Given an S3 prefix, it creates a spreadsheet with the checksums of all the objects under that prefix.
You can choose which checksum algorithms to use.

```console
$ python3 get_s3_checksums.py s3://example-bucket/photos --checksums=md5,sha1
```

This gives you a spreadsheet like:

```csv
bucket,key,size,ETag,last_modified,checksum.md5,checksum.sha1
example-bucket,photos/cat.jpg,13982,"""ec8fb43fb991a5d916ccfc96abb04b6f""",2021-10-07T07:01:20+00:00,ec8fb43fb991a5d916ccfc96abb04b6f,371ff932e114dd53eccca6e2ba28a4cc2ccb43d8
example-bucket,photos/dog.png,73859,"""445c54935453d02e93014622a5c85130""",2021-09-07T04:57:37+00:00,445c54935453d02e93014622a5c85130,86dd6ab73192d0c98da80393778493996dc87834
example-bucket,photos/emu.gif,32378,"""9ef628d1659d4a7afd75ae8db36dda10""",2021-08-19T11:29:06+00:00,9ef628d1659d4a7afd75ae8db36dda10,19a3030cbb7d9be0e65c9c6899feeb5b601ecef1
```

## Installation

You need Python 3 installed.

Clone this repository and install dependencies:

```console
$ git clone git@github.com:wellcomecollection/get_s3_checksums.git
$ cd get_s3_checksums
$ pip3 install --user requirements.txt
```

## Usage

Run the script "get_s3_checksums" in the root of the repo.

Examples:

*   Getting the checksum of every object in a bucket:

    ```console
    $ python3 get_s3_checksums.py s3://example-bucket
    checksums.example-bucket.18a0f7.csv
    ```

*   Getting the checksum of every object in a prefix within a bucket:

    ```console
    $ python3 get_s3_checksums.py s3://example-bucket/photos
    checksums.example-bucket_photos.0165fc.csv
    ```

*   By default, the script creates MD5, SHA-1, SHA-256 and SHA-512 checksums, but you can choose which checksums it creates by passing the `--checksums` parameter.
    You can use any checksum in [Python's hashlib module](https://docs.python.org/3/library/hashlib.html).

    ```console
    $ python3 get_s3_checksums.py s3://example-bucket/photos --checksums=blake2b,blake2s
    checksums.example-bucket_photos.f31404.csv
    ```

The script writes the results to a CSV spreadsheet, and prints the name of the generated spreadsheet as output.

## Recommendations

*   Run the script on an EC2 instance in the same region as your S3 bucket, not on a local machine.
    This should be faster and avoids unnecessary data transfer fees.

*   If you need checksums for multiple algorithms (e.g. SHA-256 and SHA-512), pass both checksums in the `--checksums` parameter, rather than calling the script twice.

    do:

    ```console
    $ python3 get_s3_checksums.py "$S3_PREFIX" --checksums=sha256,sha512
    ```

    don't:

    ```console
    $ python3 get_s3_checksums.py "$S3_PREFIX" --checksums=sha256
    $ python3 get_s3_checksums.py "$S3_PREFIX" --checksums=sha512
    ```

    Getting multiple checksums at once is faster and cheaper, because the object only has to be retrieved once.

## License

MIT.
