$ErrorActionPreference = 'Stop'
# Path to the folder where the script is executing
$toolsDir = (Split-Path -parent $MyInvocation.MyCommand.Definition)

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $toolsDir
    Url64bit         = 'https://download.java.net/java/GA/jmc9/05/binaries/jmc-9.1.2_windows-x64.zip'
    Checksum64       = '2ccc7fd0c10b9da90cf0ac73c12c35358f233322c4362efcb17679f556495119'
    ChecksumType64   = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
