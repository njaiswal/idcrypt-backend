#! /bin/bash

npm install -g serverless
serverless plugin install -n serverless-python-requirements
serverless deploy --stage $env --package $CODEBUILD_SRC_DIR/target/$env -v -r eu-west-1
