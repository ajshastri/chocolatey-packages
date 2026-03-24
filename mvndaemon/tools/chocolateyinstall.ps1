$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\mvndaemon"

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $targetDir = $installDir
    Url64            = 'https://github.com/apache/maven-mvnd/releases/download/1.0.5/maven-mvnd-1.0.5-windows-amd64.zip'
    Checksum64       = '15cd4716bbb0ff96d2b66607262f6145a772dcfd10b24ab18c8338d1e1f4da8e'
    ChecksumType64   = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyPath $targetDir\maven-mvnd-1.0.5-windows-amd64\bin -PathType 'Machine'
