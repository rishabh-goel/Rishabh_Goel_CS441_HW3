#!/bin/bash

cd LogFileGenerator-main &&
sbt clean compile run &&
d=$(date +%Y-%m-%d)
d='LogFileGenerator.'$d'.log'
aws s3 cp LogFileGenerator-main/log/d s3://cs441hw3