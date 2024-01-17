# Path to the folder where the script is executing
$toolsDir = (Split-Path -parent $MyInvocation.MyCommand.Definition)

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $toolsDir
    Url64bit         = 'https://download.bell-sw.com/lmc/8.3.0/bellsoft-lmc8.3.0-windows-amd64.zip'
    Checksum64       = '8eca8d45d8a6b109035dfcfc1047cd59c01501e5'
    ChecksumType64   = 'sha1'
}

Install-ChocolateyZipPackage @packageArgs
