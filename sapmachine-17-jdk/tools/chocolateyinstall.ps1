$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.21.0.3/sapmachine-jdk-17.0.21.0.3_windows-x64_bin.msi'
  Checksum64     = 'bd2d44795a1f4971f22ab130772722b4b4266ac8ca0484e00092f163c5bc8083'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
