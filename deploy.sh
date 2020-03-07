#! /bin/bash

npm install -g serverless

# Due to a bug (https://github.com/serverless/serverless/issues/5381) we have to move build into .serverless dir
mkdir -p .serverless
cp -r $CODEBUILD_SRC_DIR/target/$env/* $PWD/.serverless
serverless plugin install -n serverless-python-requirements
npm install serverless-domain-manager@3.3.1 --save-dev
npm install serverless-offline@next --save-dev
npm install --save serverless-dynamodb-local
sls plugin install -n serverless-wsgi

SLS_DEBUG=*  sls create_domain
serverless deploy --stage $env --package .serverless -v -r eu-west-1
