#!/usr/bin/python3
import os
import os.path
import json
import shutil
import subprocess
import boto3
import logging
import time
from logging.handlers import TimedRotatingFileHandler

f = open('config.json', 'r+')
configObj = json.loads(f.read())
f.close()

ddanToolsFolder = configObj["ddanToolsFolder"]
ddanInDirfolder = ddanToolsFolder + "/work/indir"

def create_timed_rotating_log(path):
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)
    
    handler = TimedRotatingFileHandler(path,
                                       when="d",
                                       interval=1,
                                       backupCount=7)
    logger.addHandler(handler)
    return logger

def clearDdanInDir(logger):
    if os.path.exists(ddanInDirfolder):
        logger.info("Cleaning DDAN indir folder (" + ddanInDirfolder + ")...")
        for filename in os.listdir(ddanInDirfolder):
            filePath = os.path.join(ddanInDirfolder, filename)
            try:
                if os.path.isfile(filePath) or os.path.islink(filePath):
                    os.unlink(filePath)
                elif os.path.isdir(filePath):
                    shutil.rmtree(filePath)
            except Exception as e:
                print('Failed to delete %s. Reason %s' % (filePath, e))


def downloadS3QuarantineBucketFiles(s3ObjectKey):
    s3Resource = boto3.resource('s3')
    s3Resource.meta.client.download_file(
        Bucket=str(os.environ.get('S3_QUARANTINE_BUCKET_NAME')),
        Key=s3ObjectKey,
        Filename= ddanToolsFolder + "/" + s3ObjectKey
    )

def listAllS3Objects(logger):
    s3Client = boto3.client('s3')
    s3ListObjectsv2Response = s3Client.list_objects_v2(
        Bucket=str(os.environ.get('S3_QUARANTINE_BUCKET_NAME'))
    )
    logger.info("Downloading files from the designation S3 Quarantine Bucket...")
    print(str(s3ListObjectsv2Response))
    return s3ListObjectsv2Response["Contents"]

def submitFilesToDDAN(logger):
    process = subprocess.Popen(
        [ddanInDirfolder + "/dtascli", "-u"],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    output = process.stdout.readline()
    logger.info(output.strip())

def main():
    logger = create_timed_rotating_log("ddan-push.log")
    logger.info("\n\nFile Storage Security - Push quarantine files to DDAN\n------------------------------------------------------------")
    logger.info("Using OS Environment variables..")
    logger.info("S3_QUARANTINE_BUCKET_NAME=" + str(os.environ.get('S3_QUARANTINE_BUCKET_NAME')))
    logger.info("DDAN_HOST=" + str(os.environ.get('DDAN_HOST')))
    logger.info("DDAN_API_KEY=" + str(os.environ.get('DDAN_API_KEY')))

    S3_QUARANTINE_BUCKET_NAME = str(os.environ.get('S3_QUARANTINE_BUCKET_NAME')) if 'S3_QUARANTINE_BUCKET_NAME' in os.environ else None
    DDAN_HOST = str(os.environ.get('DDAN_HOST')) if 'DDAN_HOST' in os.environ else None
    DDAN_API_KEY = str(os.environ.get('DDAN_API_KEY')) if 'DDAN_API_KEY' in os.environ else None

    if S3_QUARANTINE_BUCKET_NAME != None and DDAN_HOST != None and DDAN_API_KEY != None:

        # Clean up files in Deep Discovery Analyzer InDir directory
        clearDdanInDir(logger)

        s3ObjList = listAllS3Objects(logger)

        for s3Obj in s3ObjList:
            print(str(s3Obj["Key"]))
            downloadS3QuarantineBucketFiles(s3Obj["Key"])

        submitFilesToDDAN(logger)

if __name__ == "__main__":
    main()
