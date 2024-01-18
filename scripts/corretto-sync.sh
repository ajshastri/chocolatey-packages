#!/bin/bash

COMMITYES=false
BAREVERSION=21
MAILVAL=false

[[ -f /usr/bin/sed ]] && export SED="/usr/bin/sed" || export SED="/bin/sed"

function correttodl {
    JVERSION="$1"
    PACKAGE="$2"
    DLVERSIONNEW=$(curl -s -L https://api.github.com/repos/corretto/corretto-${JVERSION}/releases/latest | jq -r '.tag_name')
    VERSIONNEW=$(echo $DLVERSIONNEW | awk -F. '{print $1"."$2"."$3"."$4$5}')

    MD5NEW=$(curl -L -s https://corretto.aws/downloads/latest_checksum/amazon-corretto-${JVERSION}-x64-windows-${PACKAGE}.msi)
    # DLURL="https://corretto.aws/downloads/latest/amazon-corretto-${JVERSION}-x64-windows-${PACKAGE}.msi"
    DLURL="https://corretto.aws/downloads/resources/${DLVERSIONNEW}/amazon-corretto-${DLVERSIONNEW}-windows-x64-${PACKAGE}.msi"
    DLFILE="amazon-corretto-${DLVERSIONNEW}-windows-x64-${PACKAGE}.msi"
    echo "Latest file of ${JVERSION} is ${DLFILE} with {MD5NEW} ${MD5NEW} for ${VERSIONNEW}"

    MD5ORIG=$(grep -i checksum64 corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1 | awk -F\' '{print $2}')
    VERSIONORIG=$(grep -i -o -P '(?<=<version>).*(?=</version>)' corretto-${PACKAGE}-${JVERSION}/corretto${JVERSION}${PACKAGE}.nuspec)
    URLORIG=$(grep -i "url64" corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1 | head -1 | awk -F\' '{print $2}')

    echo "{MD5ORIG} is ${MD5ORIG}"
    if [[ "${MD5NEW}" != "${MD5ORIG}" ]]
    then
        # COMMITYES=TRUE
        echo "${MD5NEW} is not the same as ${MD5ORIG} for ${DLVERSIONNEW}"
        echo "Updating file corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1 with the new MD5"
        ${SED} -i "s@${MD5ORIG}@${MD5NEW}@g" corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1
        echo "Updating file corretto-${PACKAGE}-${JVERSION}/corretto${JVERSION}${PACKAGE}.nuspec with the new version - ${VERSIONORIG} to ${VERSIONNEW}"
        ${SED} -i "s@${VERSIONORIG}@${VERSIONNEW}@g" corretto-${PACKAGE}-${JVERSION}/corretto${JVERSION}${PACKAGE}.nuspec
        echo "Updating file corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1 with the new URL - ${URLORIG} to ${DLURL}"
        ${SED} -i "s@${URLORIG}@${DLURL}@g" corretto-${PACKAGE}-${JVERSION}/tools/chocolateyinstall.ps1

        # Section for corretto-${PACKAGE}
        if [[ "$JVERSION" == "$BAREVERSION" ]]
        then
            echo "Updating file corretto-${PACKAGE}/tools/chocolateyinstall.ps1 with the new MD5"
            ${SED} -i "s@${MD5ORIG}@${MD5NEW}@g" corretto-${PACKAGE}/tools/chocolateyinstall.ps1
            echo "Updating file corretto-${PACKAGE}/corretto${PACKAGE}.nuspec with the new version - ${VERSIONORIG} to ${VERSIONNEW}"
            ${SED} -i "s@${VERSIONORIG}@${VERSIONNEW}@g" corretto-${PACKAGE}/corretto${PACKAGE}.nuspec
            echo "Updating file corretto-${PACKAGE}/tools/chocolateyinstall.ps1 with the new URL - ${URLORIG} to ${DLURL}"
            ${SED} -i "s@${URLORIG}@${DLURL}@g" corretto-${PACKAGE}/tools/chocolateyinstall.ps1
        fi

        echo "Latest file of ${JVERSION} is ${DLFILE} with {MD5NEW} ${MD5NEW} for ${DLVERSIONNEW}"
        MAILVAL=true
    fi
}

for JVERSION in {8,11,17,21}
do
    correttodl ${JVERSION} jdk
done

correttodl 8 jre

