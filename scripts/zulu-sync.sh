#!/bin/bash

COMMITYES=false
ZBAREVERSION=17
OSTYPE=windows #linux
ARCHIVETYPE=msi #tar.gz
ARCHTYPE=x64
ZPACK=jdk
CRACV=false
MAILVAL=false
FXVAL=true

echo "Newest versions and DL files are:"

for JVERSION in {8,11,17,21}
do
    echo "CRAC value for ${JVERSION} is ${CRACV}"
    UUID=$(curl -s -X GET "https://api.azul.com/metadata/v1/zulu/packages/?java_version=${JVERSION}&os=${OSTYPE}&arch=${ARCHTYPE}&archive_type=${ARCHIVETYPE}&java_package_type=${ZPACK}&javafx_bundled=${FXVAL}&latest=true&distro_version=${JVERSION}&release_status=ga&crac_supported=${CRACV}&availability_types=CA&certifications=tck&page=1&page_size=1" -H "accept: application/json" | jq -r .[0].package_uuid)
    SHA256NEW=$(curl -s -X GET "https://api.azul.com/metadata/v1/zulu/packages/${UUID}" -H "accept: application/json" | jq -r .sha256_hash)
    DLURL=$(curl -s -X GET "https://api.azul.com/metadata/v1/zulu/packages/${UUID}" -H "accept: application/json" | jq -r .download_url)
    DLFILE=$(curl -s -X GET "https://api.azul.com/metadata/v1/zulu/packages/${UUID}" -H "accept: application/json" | jq  -r .name)
    ZVERSIONNEW=$(curl -s -X GET "https://api.azul.com/metadata/v1/zulu/packages/${UUID}" -H "accept: application/json" | jq .distro_version[] | sed -z s@\\n@\.@g| sed 's/\.*$//g')
    echo "Latest file of ${JVERSION} is ${DLFILE} with SHA256NEW $SHA256NEW for $ZVERSIONNEW"

    SHA256ORIG=$(grep checksum64 zulu-${JVERSION}/tools/chocolateyinstall.ps1 | awk -F\' '{print $2}')
    ZVERSIONORIG=$(grep -o -P '(?<=<version>).*(?=</version>)' zulu-${JVERSION}/zulu-${JVERSION}.nuspec)
    URLORIG=$(grep "\$url64" zulu-${JVERSION}/tools/chocolateyinstall.ps1 | head -1 | awk -F\' '{print $2}')
    echo "SHA256ORIG is $SHA256ORIG"
    if [[ "$SHA256NEW" != "$SHA256ORIG" ]]
    then
        # COMMITYES=TRUE
        echo "$SHA256NEW is not the same as $SHA256ORIG for $ZVERSIONNEW"
        sed -i "s@$SHA256ORIG@$SHA256NEW@g" zulu-${JVERSION}/tools/chocolateyinstall.ps1
        sed -i "s@$ZVERSIONORIG@$ZVERSIONNEW@g" zulu-${JVERSION}/zulu-${JVERSION}.nuspec
        sed -i "s@$URLORIG@$DLURL@g" zulu-${JVERSION}/tools/chocolateyinstall.ps1
        if [[ "$ZBAREVERSION" == "17" ]]
        then
            sed -i "s@$SHA256ORIG@$SHA256NEW@g" zulu/tools/chocolateyinstall.ps1
            sed -i "s@$ZVERSIONORIG@$ZVERSIONNEW@g" zulu/zulu.nuspec
            sed -i "s@$URLORIG@$DLURL@g" zulu/tools/chocolateyinstall.ps1
        fi
        echo "Latest file of ${JVERSION} is ${DLFILE} with SHA256NEW $SHA256NEW for $ZVERSIONNEW"
        MAILVAL=true
    fi
done

