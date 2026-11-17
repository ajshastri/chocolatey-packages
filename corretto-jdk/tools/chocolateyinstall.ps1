$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/25.0.5.1.2/amazon-corretto-25.0.5.1.2-windows-x64.msi'
  Checksum64 = 'ded32dedfc8a2e3d15017700e29ecb08edb29b3a852c82ee3d6443dc9c354b61'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
