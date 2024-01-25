$ErrorActionPreference = 'Stop'
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"

$url64      = 'https://cdn.azul.com/zulu/bin/zulu17.46.19-ca-fx-jdk17.0.9-win_x64.msi'

$packageArgs = @{
  packageName   = $env:ChocolateyPackageName
  unzipLocation = $toolsDir
  fileType      = 'msi'
  url           = $url
  url64bit      = $url64

  softwareName  = 'Zulu*'
  checksum64    = '2332e27b754778deaa6201e57f59b374b0d556bf4fa89c30ea32df34a3165227'
  checksumType64= 'sha256'

  silentArgs    = "ADDLOCAL=ZuluInstallation,FeatureEnvironment /qn /norestart"
  validExitCodes= @(0)
}

Install-ChocolateyPackage @packageArgs
