#!/usr/bin/python3
import os
import os.path
import subprocess
import boto3

ddanInDirFolder = '~/ddan/work/indir/'

def clearDdanInDir():
    if os.path.exists(ddanInDirFolder):
        os.rmdir(ddanInDirFolder)

def downloadS3QuarantineBucketFiles(s3ObjectKey):
    s3Resource = boto3.resource('s3')
    s3Resource.meta.client.download_file(
        Bucket=str(os.environ.get('S3_QUARANTINE_BUCKET_NAME')),
        Key=s3ObjectKey,
        Filename= ddanInDirFolder + s3ObjectKey
    )

def listAllS3Objects():
    s3Client = boto3.client('s3')
    s3ListObjectsv2Response = s3Client.list_objects_v2(
        Bucket=str(os.environ.get('S3_QUARANTINE_BUCKET_NAME'))
    )
    print(str(s3ListObjectsv2Response))

    return s3ListObjectsv2Response["Contents"]

def submitFilesToDDAN():
    process = subprocess.Popen(
        ['~/ddan/dtascli', '-u'],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    output = process.stdout.readline()
    print(output.strip())

def main():
    print("\n\nFile Storage Security - Push quarantine files to DDAN\n------------------------------------------------------------")
    print(str(os.environ.get('S3_QUARANTINE_BUCKET_NAME')))
    print(str(os.environ.get('DDAN_HOST')))
    print(str(os.environ.get('DDAN_API_KEY')))

    # Clean up files in Deep Discovery Analyzer InDir directory
    clearDdanInDir()

    s3ObjList = listAllS3Objects()

    for s3Obj in s3ObjList:
        print(str(s3Obj["Key"]))
        downloadS3QuarantineBucketFiles(s3Obj["Key"])

    submitFilesToDDAN()
