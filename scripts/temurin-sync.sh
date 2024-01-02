#!/bin/bash

function dljdkfileinfo() {
  curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jdks?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename |  contains ("full") | not) | select(.filename |  contains ("lite") | not)';
}

function dljrefileinfo() {
  curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jres?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename |  contains ("full") | not) | select(.filename |  contains ("lite") | not)';
}


#JAVATYPE is JDK regular
# JVERSION=21
JAVATYPE=jdk
for JVERSION in {8,11,17,21}
do
    # temurin regular full
    DLDEETS=$(dljdkfileinfo $JVERSION temurin)
    VERSIONNEW=$(echo $DLDEETS | jq -r '.java_version' | tr '+' '.')
    JAVADEETS=$(curl -s -L -X 'GET' $(echo $DLDEETS | jq -r '.links.pkg_info_uri'))
    JAVAFILE=$(echo $JAVADEETS | jq -r .result[].filename)
    CHECKSUMTYPE=$(echo $JAVADEETS | jq -r .result[].checksum_type)
    DLURL=$(echo $JAVADEETS | jq -r ".result[].direct_download_uri")
    TEMFOLDNAME=temurin-${JVERSION}-${JAVATYPE}
    
    SHA256NEW=$(echo $JAVADEETS | jq -r .result[].checksum)
    
    SHA256ORIG=$(grep -i checksum64 ${TEMFOLDNAME}/tools/chocolateyinstall.ps1 | awk -F\' '{print $2}')
    VERSIONORIG=$(grep -i -o -P '(?<=<version>).*(?=</version>)' ${TEMFOLDNAME}/temurin${JVERSION}${JAVATYPE}.nuspec)
    URLORIG=$(grep -i "url64" ${TEMFOLDNAME}/tools/chocolateyinstall.ps1 | head -1 | awk -F\' '{print $2}')
    
    echo "$JVERSION $JAVATYPE has SHA256ORIG $SHA256ORIG and SHA256NEW $SHA256NEW"
    if [[ "$SHA256NEW" != "$SHA256ORIG" ]]
    then
        # COMMITYES=TRUE
        echo "$SHA256NEW is not the same as $SHA256ORIG for $VERSIONNEW"
        sed -i "s@$SHA256ORIG@$SHA256NEW@g" ${TEMFOLDNAME}/tools/chocolateyinstall.ps1
        sed -i "s@$VERSIONORIG@$VERSIONNEW@g" ${TEMFOLDNAME}/temurin${JVERSION}${JAVATYPE}.nuspec
        sed -i "s@$URLORIG@$DLURL@g" ${TEMFOLDNAME}/tools/chocolateyinstall.ps1
        if [[ "$JVERSION" == "21" ]]
        then
            sed -i "s@$SHA256ORIG@$SHA256NEW@g" temurin-${JAVATYPE}/tools/chocolateyinstall.ps1
            sed -i "s@$VERSIONORIG@$VERSIONNEW@g" temurin-${JAVATYPE}/temurin${JAVATYPE}.nuspec
            sed -i "s@$URLORIG@$DLURL@g" temurin-${JAVATYPE}/tools/chocolateyinstall.ps1
        fi
        echo "Latest file of ${JVERSION} is ${JAVAFILE} with SHA256NEW $SHA256NEW for $VERSIONNEW"
        MAILVAL=true
    fi
done