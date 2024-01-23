$ErrorActionPreference  = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/bell-sw/Liberica/releases/download/21.0.2+14/bellsoft-jdk21.0.2+14-windows-amd64-lite.msi'
  Checksum64 = 'c075b20e6c77f3c7b50a8447aa59a1919eaf4f43'
  ChecksumType64 = 'sha1'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
