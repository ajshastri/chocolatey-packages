$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-17.0.10/sapmachine-jre-17.0.10_windows-x64_bin.msi'
  Checksum64 = '234fe259e500cc5dec31a8deacefbefdbe7b43c0be1c6b60e2a4b848b9382ca6'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
