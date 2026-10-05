$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\WildFly"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url = 'https://github.com/wildfly/wildfly/releases/download/41.0.1.Final/wildfly-41.0.1.Final.zip'
    Checksum = '783e6405a132a1f088b1a8f885040ef1e0ae3976a788a992147bc3e443dfe1b6'
    ChecksumType = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
