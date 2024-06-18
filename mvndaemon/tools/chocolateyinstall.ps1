$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\mvndaemon"

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $targetDir = $installDir
    Url64            = 'https://github.com/apache/maven-mvnd/releases/download/1.0.0/maven-mvnd-1.0.0-windows-amd64.zip'
    Checksum64       = '0ccc62bd1633f9655cef6ff11a081424a639e1a2d023535322967e1419c4638b'
    ChecksumType64   = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyPath $targetDir\maven-mvnd-1.0.0-windows-amd64\bin -PathType 'Machine'
