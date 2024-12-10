#!/usr/bin/env python3

import click
import tempfile
import logging
import sys
import s3_to_local_stamps

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)-15s %(filename)s:%(lineno)d %(levelname)s: %(message)s",
    force=True,
)


@click.command(help="Compress and upload an S3 file.")
@click.argument("s3_path", type=str)
@click.option(
    "--local-path",
    default=None,
    help=(
        "Local path to save the file temporarily. If not provided, a temporary path"
        " will be used."
    ),
)
@click.option(
    "--new-s3-path",
    default=None,
    help=(
        "New S3 path to upload the compressed file. If not provided, the original S3"
        " path will be used."
    ),
)
@click.option(
    "--new-bucket",
    default=None,
    help=(
        "New S3 bucket to upload the compressed file. If not provided, the original"
        " bucket will be used."
    ),
)
@click.option(
    "--strip-local-extension",
    default=None,
    help=(
        "Extension to strip from the local path before saving the file. Useful if the"
        " S3 file has an extension that should be removed locally."
    ),
)
def compress_s3_key(
    s3_path, local_path, new_s3_path, new_bucket, strip_local_extension=".bz2"
):
    """
    Compress and upload an S3 file.

    This script downloads a file from the specified S3 path, compresses it using bz2,
    and uploads it back to S3. The original file can be overwritten or saved to a new
    location.

    \b
    Arguments:
        s3_path: The S3 path to the file to be compressed and uploaded.

    \b
    Options:
        --local-path: Local path to save the file temporarily.
        --new-s3-path: New S3 path to upload the compressed file.
        --new-bucket: New S3 bucket to upload the compressed file.
        --strip-local-extension: Extension to strip from the local path.
    """
    if local_path is None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            local_path = temp_file.name
    s3compressor = s3_to_local_stamps.S3Compressor(
        s3_path,
        local_path=local_path,
        new_s3_path=new_s3_path,
        new_bucket=new_bucket,
        strip_local_extension=strip_local_extension,
    )
    s3compressor.compress_and_upload()


if __name__ == "__main__":
    compress_s3_key()
    sys.exit(0)
