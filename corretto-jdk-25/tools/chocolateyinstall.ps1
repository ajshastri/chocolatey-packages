$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/25.0.4.10.1/amazon-corretto-25.0.4.10.1-windows-x64.msi'
  Checksum64 = '23b18e6f346abbad2655cb492292d5071a7ec28b3057c2911239968751ed908e'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
