$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://corretto.aws/downloads/resources/8.504.04.1/amazon-corretto-8.504.04.1-windows-x64-jdk.msi'
  Checksum64 = 'b8cea3ab5298c8e2402af17f79251a75d61b1903a19cce18f6f8ead1c42d82cf'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
