#!/bin/bash
set -e

cd /tmp
wget -q https://github.com/oclint/oclint/releases/download/v22.02/oclint-22.02-llvm-13.0.1-x86_64-linux-ubuntu-20.04.tar.gz
tar -xzf oclint-*.tar.gz

mkdir -p /opt/oclint
cp -r oclint-22.02/* /opt/oclint/

rm -rf oclint-*