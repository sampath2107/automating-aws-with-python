#!/usr/python/bin

from botocore.exceptions import ClientError
import mimetypes
from pathlib import Path
import boto3
import sys
import click


session=boto3.Session(profile_name='pythonAutomation')
s3 =session.resource('s3')

@click.group()
def cli():
    pass

@cli.command('list-buckets')
def list_buckets():
    """List All buckets"""
    for bucket in s3.buckets.all():
        print (bucket)

@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List All objects in an S3 bucket"""
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """create and configure s3 bucket"""
    s3_bucket= None
    try:
        s3_bucket=s3.create_bucket(Bucket=bucket)
    except ClientError as e:
        if e.response['Error']['Code']=='BucketAlreadyOwnedByYou':
            s3_bucket=s3.Bucket(bucket)
        else:
            raise e
    policy="""{
    "Version":"2012-10-17",
    "Statement":[{
    "Sid":"PublicReadGetObject",
    "Effect":"Allow",
    "Principal": "*",
    "Action":["s3:GetObject"],
    "Resource":["arn:aws:s3:::%s/*"]
        }
        ]
        }
        """% s3_bucket.name


    pol = s3_bucket.Policy()
    pol.put(Policy=policy)
    s3_bucket.Website().put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }})
    return
def upload_file(s3_bucket,path,key):
    content_type=mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upload_file(path,key,ExtraArgs={'ContentType': content_type})

@cli.command('sync')
@click.argument('pathname',type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname,bucket):
    """sync contents of PATHNAME to BUCKET"""
    s3_bucket= s3.Bucket(bucket)

    root =Path(pathname).expanduser().resolve()
    def handle_directory(target):
        for p in target.iterdir():
            if p.is_dir():handle_directory(p)
            if p.is_file():
                upload_file(s3_bucket,str(p),str(p.relative_to(root)))

    handle_directory(root)

if __name__=='__main__':
    cli()
