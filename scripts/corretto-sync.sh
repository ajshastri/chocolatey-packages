#!/bin/bash

COMMITYES=false
BAREVERSION=21
MAILVAL=false


function correttodl{
    JVERSION=$1
    PACKAGE=$2
    VERSIONNEW=$(curl -s -L https://api.github.com/repos/corretto/corretto-${JVERSION}/releases/latest | jq -r '.tag_name')
    MD5NEW=$(curl -L -s https://corretto.aws/downloads/latest_checksum/amazon-corretto-${JVERSION}-x64-windows-${PACKAGE}.msi)
    # DLURL="https://corretto.aws/downloads/latest/amazon-corretto-${JVERSION}-x64-windows-${PACKAGE}.msi"
    DLURL="https://corretto.aws/downloads/resources/${VERSIONNEW}/amazon-corretto-${VERSIONNEW}-windows-x64-${PACKAGE}.msi"
    DLFILE="amazon-corretto-${VERSIONNEW}-windows-x64-${PACKAGE}.msi"
    echo "Latest file of ${JVERSION} is ${DLFILE} with MD5NEW $MD5NEW for $VERSIONNEW"

    MD5ORIG=$(grep checksum64 corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1 | awk -F\' '{print $2}')
    VERSIONORIG=$(grep -o -P '(?<=<version>).*(?=</version>)' corretto-${PACKAGE}-${JVERSION}/corretto${JVERSION}${PACKAGE}.nuspec)
    URLORIG=$(grep "\$url64" corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1 | head -1 | awk -F\' '{print $2}')
    
    echo "MD5ORIG is $MD5ORIG"
    if [[ "$MD5NEW" != "$MD5ORIG" ]]
    then
        # COMMITYES=TRUE
        echo "$MD5NEW is not the same as $MD5ORIG for $VERSIONNEW"
        sed -i "s@$MD5ORIG@$MD5NEW@g" corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1
        sed -i "s@$VERSIONORIG@$VERSIONNEW@g" corretto-${PACKAGE}-${JVERSION}/corretto${JVERSION}${PACKAGE}.nuspec)
        sed -i "s@$URLORIG@$DLURL@g" corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1
        
        # Section for corretto-${PACKAGE}
        if [[ "$JVERSION" == "$BAREVERSION" ]]
        then
            sed -i "s@$MD5ORIG@$MD5NEW@g" corretto-${PACKAGE}/tools/chocolateyinstall.ps1
            sed -i "s@$VERSIONORIG@$VERSIONNEW@g" corretto-${PACKAGE}/corretto${PACKAGE}.nuspec
            sed -i "s@$URLORIG@$DLURL@g" corretto-${PACKAGE}/tools/chocolateyinstall.ps1
        fi

        echo "Latest file of ${JVERSION} is ${DLFILE} with MD5NEW $MD5NEW for $VERSIONNEW"
        MAILVAL=true
    fi
}

for JVERSION in {8,11,17,21}
do
    correttodl $JVERSION jdk
done

correttodl 8 jre
