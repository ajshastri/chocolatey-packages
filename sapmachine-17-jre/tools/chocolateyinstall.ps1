$ErrorActionPreference = 'Stop'
$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.12/sapmachine-jre-17.0.12_windows-x64_bin.msi'
  Checksum64 = '69cafc67d68e4f4e8d2f97857cd7cbfa8e9f30d4ba7346f4fb7af8fef402972d'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
