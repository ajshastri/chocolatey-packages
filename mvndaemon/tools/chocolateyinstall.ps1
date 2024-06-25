$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\mvndaemon"

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $targetDir = $installDir
    Url64            = 'https://github.com/apache/maven-mvnd/releases/download/1.0.1/maven-mvnd-1.0.1-windows-amd64.zip'
    Checksum64       = '5a4a05fa6394b6fca0f88e18aa87682e64ce41923b057ca611ea25eb4405d34c'
    ChecksumType64   = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyPath $targetDir\maven-mvnd-1.0.0-windows-amd64\bin -PathType 'Machine'
