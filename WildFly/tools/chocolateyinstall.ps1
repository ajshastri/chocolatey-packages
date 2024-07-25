$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\WildFly"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url = 'https://github.com/wildfly/wildfly/releases/download/33.0.0.Final/wildfly-33.0.0.Final.zip'
    Checksum = '85cb39ece24cc5f540e30893ebda338643c49acb'
    ChecksumType = 'sha1'
}

Install-ChocolateyZipPackage @packageArgs
