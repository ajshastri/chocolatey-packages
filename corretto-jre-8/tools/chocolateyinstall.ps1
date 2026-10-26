$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.512.08.1/amazon-corretto-8.512.08.1-windows-x64-jre.msi'
  Checksum64 = '341acbb9af921932f69b866eda183ec32e287dad48b3c6bb0919ac70178d3f82'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
