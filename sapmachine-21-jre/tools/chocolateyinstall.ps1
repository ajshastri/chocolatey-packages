$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit       = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.13.0.2/sapmachine-jre-21.0.13.0.2_windows-x64_bin.msi'
  Checksum64     = '73136152df6033297af7c61d91d42d954faf327ccde821ccda415575ec1c7042'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
