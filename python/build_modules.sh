#!/bin/bash
set -e

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
echo "Installing $SCRIPTPATH/envgene"
pip install $SCRIPTPATH/envgene
echo "Removing build trash..."
rm -r $SCRIPTPATH/envgene/build
rm -r $SCRIPTPATH/envgene/envgenehelper.egg-info
echo "Installing $SCRIPTPATH/jschon-sort"
pip install $SCRIPTPATH/jschon-sort
echo "Removing build trash..."
rm -r $SCRIPTPATH/jschon-sort/build
rm -r $SCRIPTPATH/jschon-sort/jschon_sort.egg-info
echo "Installing $SCRIPTPATH/integration"
pip install $SCRIPTPATH/integration
echo "Removing build trash..."
rm -r $SCRIPTPATH/integration/build
rm -r $SCRIPTPATH/integration/integration_loader.egg-info