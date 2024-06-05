$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\WildFly"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url = 'https://github.com/wildfly/wildfly/releases/download/32.0.1.Final/wildfly-32.0.1.Final.zip'
    Checksum = 'b97930b3b7c99f800df2d3913416f350b12986ab'
    ChecksumType = 'sha1'
}

Install-ChocolateyZipPackage @packageArgs
