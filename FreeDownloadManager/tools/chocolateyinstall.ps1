$ErrorActionPreference = 'Stop';
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://files2.freedownloadmanager.org/fdm6_qt5/fdm_x86_setup.exe'
$url64      = 'https://files2.freedownloadmanager.org/fdm6_qt5/fdm_x64_setup.exe'

$packageArgs = @{
  packageName   = 'FreeDownloadManager'
  unzipLocation = $toolsDir
  fileType      = 'EXE'
  url           = $url
  url64bit      = $url64
  softwareName  = 'FreeDownloadManager*'
  checksum      = '4af36a3093cf0bf8ad7bb3258d882b295303a60f95439ed15194d3fd38ab2f1a'
  checksumType  = 'sha256'
  checksum64    = 'cbc661c7a1e108919e58e882e1f9df2819ca4a2c5035f2b089420d96aa37d8e1'
  checksumType64= 'sha256'
  
  validExitCodes= @(0, 3010, 1641)
  silentArgs   = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-'
}

Install-ChocolateyPackage @packageArgs










    








