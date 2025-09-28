$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\mvndaemon"

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $targetDir = $installDir
    Url64            = 'https://github.com/apache/maven-mvnd/releases/download/1.0.2/maven-mvnd-1.0.2-windows-amd64.zip'
    Checksum64       = 'c48cdbee495b6d93a171648801a4485bef10f1f0d0ee3eb64a5ee67f8ae77461'
    ChecksumType64   = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyPath $targetDir\maven-mvnd-1.0.2-windows-amd64\bin -PathType 'Machine'
