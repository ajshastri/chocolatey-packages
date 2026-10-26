$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.21.0.2/sapmachine-jre-17.0.21.0.2_windows-x64_bin.msi'
  Checksum64     = '88e362ce69e0ced33a8031d58cab097cc05ffc1d6e0fea0a3a636209568b9952'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
