$ErrorActionPreference = 'Stop';
$toolsDir   = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url        = 'https://dn3.freedownloadmanager.org/6/latest/fdm_x86_setup.exe'
$url64      = 'https://dn3.freedownloadmanager.org/6/latest/fdm_x64_setup.exe'

$packageArgs = @{
  packageName   = 'FreeDownloadManager'
  unzipLocation = $toolsDir
  fileType      = 'EXE'
  url           = $url
  url64bit      = $url64
  softwareName  = 'FreeDownloadManager*'
  checksum      = '4af36a3093cf0bf8ad7bb3258d882b295303a60f95439ed15194d3fd38ab2f1a'
  checksumType  = 'sha256'
  checksum64    = 'eeabadf6a6cb772f3356f4e4eebaeabe204a57e0946d26a904dc8cc79cbdc328'
  checksumType64= 'sha256'
  
  validExitCodes= @(0, 3010, 1641)
  silentArgs   = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-'
}

Install-ChocolateyPackage @packageArgs










    








