$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\WildFly"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url = 'https://github.com/wildfly/wildfly/releases/download/33.0.0.Final/wildfly-33.0.0.Final.zip'
    Checksum = '6fe811183dd1cb6e369f93c5ec3b4c4ac3c99266'
    ChecksumType = 'sha1'
}

Install-ChocolateyZipPackage @packageArgs
