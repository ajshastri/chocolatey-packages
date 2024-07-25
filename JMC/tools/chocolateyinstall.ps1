$ErrorActionPreference = 'Stop'
# Path to the folder where the script is executing
$toolsDir = (Split-Path -parent $MyInvocation.MyCommand.Definition)

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $toolsDir
    Url64bit         = 'https://download.java.net/java/GA/jmc9/10/binaries/jmc-9.0.0_windows-x64.zip'
    Checksum64       = 'afbf176b0d25427168b3fa3db9df0f099d715d9463686995d238bac70b87cf47'
    ChecksumType64   = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
