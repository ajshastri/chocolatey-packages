$packageArgs = @{
  PackageName = $env:ChocolateyPackageName
  Url64bit = 'https://github.com/SAP/SapMachine/releases/download/sapmachine-21.0.2/sapmachine-jre-21.0.2_windows-x64_bin.msi'
  Checksum64 = '14dcbc01f4c34d4c72ed83292f60f6f5b2d29960bdabf4e3bbfbf1b7d26e86d1'
  ChecksumType64 = 'sha256'
  fileType      = 'msi'
  silentArgs    = "INSTALLLEVEL=3 /quiet"
}

Install-ChocolateyPackage @packageArgs
