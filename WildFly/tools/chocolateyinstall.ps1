$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\WildFly"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url = 'https://github.com/wildfly/wildfly/releases/download/37.0.1.Final/wildfly-37.0.1.Final.zip'
    Checksum = 'bbb9722f7d55e07f034f02ec08f9902c5262eb6ce2bb61bc929cba3cf08c054c'
    ChecksumType = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
