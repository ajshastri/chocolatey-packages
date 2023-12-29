#!/bin/bash


function dljdkfileinfofull() {
  curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jdks?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename | contains ("full"))';
}

function dljdkfileinfofull() {
  URL=$(curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jdks?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename | contains ("full")) | .links.pkg_info_uri');
  curl -s -L -X 'GET' $URL;
}

function dljdkfileinfolite() {
  URL=$(curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jdks?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename | contains ("lite")) | .links.pkg_info_uri');
  curl -s -L -X 'GET' $URL;
}

function dljdkfileinforeg() {
  URL=$(curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jdks?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[] | select(.filename |  contains ("full") | not) | select(.filename |  contains ("lite") | not) | .links.pkg_info_uri')
  curl -s -L -X 'GET' $URL;
}

function dljrefileinfo() {
  URL=$(curl -s -L -X 'GET' "https://api.foojay.io/disco/v3.0/packages/jres?version=${1}&distribution=${2}&architecture=amd64&archive_type=msi&operating_system=windows&latest=available" -H 'accept: application/json' | jq -r '.result[].links.pkg_info_uri')
  curl -s -L -X 'GET' $URL ;
}


JVERSION=11
JAVATYPE=jdkfull
# Liberica regular
DLDEETS=$(dljdkfileinfofull 11 liberica)
VERSIONNEW=$(echo $DLDEETS | jq -r '.java_version' | tr '+' '.')
JAVADEETS=$(curl -s -L -X 'GET' $(echo $DLDEETS | jq -r '.links.pkg_info_uri'))
JAVAFILE=$(echo $JAVADEETS | jq -r .result[].filename)
CHECKSUMTYPE=$(echo $JAVADEETS | jq -r .result[].checksum_type)
DLURL=$(echo $JAVADEETS | jq -r ".result[].direct_download_uri")
LIBERFOLDNAME=liberica-${JAVATYPE}-${JVERSION}
if [[ "$CHECKSUMTYPE" != "sha256" ]]
then
  curl -L -o ${JAVAFILE} $(echo $JAVADEETS | jq -r .result[].direct_download_uri)
  SHA256NEW=$(sha256sum ${JAVAFILE} | awk '{print $1}')
  rm -f ${JAVAFILE}
else
  SHA256FILEURL=$(echo $JAVADEETS | jq -r .result[].checksum_uri)
  SHA256NEW=$(curl -s -L $SHA256FILEURL | awk '{print $1}')
fi

SHA256ORIG=$(grep -i checksum64 ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1 | awk -F\' '{print $2}')
VERSIONORIG=$(grep -i -o -P '(?<=<version>).*(?=</version>)' ${LIBERFOLDNAME}/liberica${JVERSION}${JAVATYPE}.nuspec)
URLORIG=$(grep -i "\$url64" ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1 | head -1 | awk -F\' '{print $2}')

if [[ "$SHA256NEW" != "$SHA256ORIG" ]]
then
    # COMMITYES=TRUE
    echo "$SHA256NEW is not the same as $SHA256ORIG for $VERSIONNEW"
    sed -i "s@$SHA256ORIG@$SHA256NEW@g" ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1
    sed -i "s@$VERSIONORIG@$VERSIONNEW@g" ${LIBERFOLDNAME}/liberica${JVERSION}${JAVATYPE}.nuspec
    sed -i "s@$URLORIG@$DLURL@g" ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1
    if [[ "$ZBAREVERSION" == "17" ]]
    then
        sed -i "s@$SHA256ORIG@$SHA256NEW@g" ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1
        sed -i "s@$VERSIONORIG@$VERSIONNEW@g" ${LIBERFOLDNAME}/liberica.nuspec
        sed -i "s@$URLORIG@$DLURL@g" ${LIBERFOLDNAME}/tools/chocolateyinstall.ps1
    fi
    echo "Latest file of ${JVERSION} is ${JAVAFILE} with SHA256NEW $SHA256NEW for $VERSIONNEW"
    MAILVAL=true
    fi
done