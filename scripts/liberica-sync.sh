#!/bin/bash


function dljdkfileinfofull() {
  curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jdks?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename | contains ("full"))';
}

function dljdkfileinfolite() {
  curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jdks?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename | contains ("lite"))';
}

function dljdkfileinforeg() {
  curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jdks?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename |  contains ("full") | not) | select(.filename |  contains ("lite") | not)';
}

function dljrefileinfo() {
  curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jres?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename |  contains ("full") | not) | select(.filename |  contains ("lite") | not)';
}

function dljrefileinfofull() {
  curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jres?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename | contains ("full"))';
}

JAVATYPE=jdkfull
# JVERSION=21
for JVERSION in {11,17,21}
do
    # Liberica regular full
    DLDEETS=$(dljdkfileinfofull $JVERSION liberica)
    VERSIONNEW=$(echo $DLDEETS | jq -r '.java_version' | tr '+' '.')
    JAVADEETS=$(curl -s -L -X 'GET' $(echo $DLDEETS | jq -r '.links.pkg_info_uri'))
    JAVAFILE=$(echo $JAVADEETS | jq -r .result[].filename)
    CHECKSUMTYPE=$(echo $JAVADEETS | jq -r .result[].checksum_type)
    DLURL=$(echo $JAVADEETS | jq -r ".result[].direct_download_uri")
    LIBERFOLDNAME=liberica-${JVERSION}-${JAVATYPE}
    
    SHA1NEW=$(echo $JAVADEETS | jq -r .result[].checksum)
    
    SHA1ORIG=$(grep -i checksum64 ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1 | awk -F\' '{print $2}')
    VERSIONORIG=$(grep -i -o -P '(?<=<version>).*(?=</version>)' ${LIBERFOLDNAME}/liberica${JVERSION}${JAVATYPE}.nuspec)
    URLORIG=$(grep -i "url64" ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1 | head -1 | awk -F\' '{print $2}')
    
    echo "$JVERSION $JAVATYPE has SHA1ORIG $SHA1ORIG and SHA1NEW $SHA1NEW"
    if [[ "$SHA1NEW" != "$SHA1ORIG" ]]
    then
        # COMMITYES=TRUE
        echo "$SHA1NEW is not the same as $SHA1ORIG for $VERSIONNEW"
        sed -i "s@$SHA1ORIG@$SHA1NEW@g" ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1
        sed -i "s@$VERSIONORIG@$VERSIONNEW@g" ${LIBERFOLDNAME}/liberica${JVERSION}${JAVATYPE}.nuspec
        sed -i "s@$URLORIG@$DLURL@g" ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1
        if [[ "$JVERSION" == "21" ]]
        then
            sed -i "s@$SHA1ORIG@$SHA1NEW@g" liberica-${JAVATYPE}/tools/chocolateyinstall.ps1
            sed -i "s@$VERSIONORIG@$VERSIONNEW@g" liberica-${JAVATYPE}/liberica${JAVATYPE}.nuspec
            sed -i "s@$URLORIG@$DLURL@g" liberica-${JAVATYPE}/tools/chocolateyinstall.ps1
        fi
        echo "Latest file of ${JVERSION} is ${JAVAFILE} with SHA1NEW $SHA1NEW for $VERSIONNEW"
        MAILVAL=true
    fi
done  
