#!/bin/bash
set -e

# Start servers
nohup serverless dynamodb start --stage test & echo $! > pidfile1
nohup moto_server s3 -p4500 & echo $! > pidfile2
service elasticsearch start

# Start Dynamodb triggers
nohup python dbStreamRunner.py -t Requests-test -l triggers.requestProcessor & echo $! > pidfile4
nohup python dbStreamRunner.py -t Docs-test -l triggers.docProcessor & echo $! > pidfile5

# Start S3 triggers
nohup python s3UploadsProcessRunner.py & echo $! > pidfile6

# Tail all server/trigger log files
tail -n 10000 -F nohup.out & echo $! > pidfile7
