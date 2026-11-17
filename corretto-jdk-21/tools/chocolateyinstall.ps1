$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/21.0.13.1.2/amazon-corretto-21.0.13.1.2-windows-x64.msi'
  Checksum64 = 'fd52d8bbc21f715e0f865f468f3420170a7bc3edf16aab0baeb630a3a432dff3'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
