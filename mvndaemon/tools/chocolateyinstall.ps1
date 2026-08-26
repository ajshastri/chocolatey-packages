$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\mvndaemon"

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $targetDir = $installDir
    Url64            = 'https://github.com/apache/maven-mvnd/releases/download/1.0.6/maven-mvnd-1.0.6-windows-amd64.zip'
    Checksum64       = 'caba9e00736b8c0c62b9238ee75bc64294a0df42e45ecd513fee1914da3fd6cf'
    ChecksumType64   = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyPath $targetDir\maven-mvnd-1.0.6-windows-amd64\bin -PathType 'Machine'
