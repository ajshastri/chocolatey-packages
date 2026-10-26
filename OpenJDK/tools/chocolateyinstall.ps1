$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\OpenJDK"

$version = "27.0.1.0.3"

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $targetDir = $installDir
    Url64            = 'https://download.java.net/java/GA/jdk27.0.1.0.3/b14170c9b2de463d9b89442c6db3e384/1/GPL/openjdk-27.0.1.0.3_windows-x64_bin.zip'
    Checksum64       = '028d4866d96312a25fc5dd8c1bc107f6f365ef8a9ff32b7e0687257623a7f98f'
    ChecksumType64   = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyEnvironmentVariable 'JAVA_HOME' $targetDir\jdk-$version 'Machine'
# The full path instead of the %JAVA_HOME% is needed so it can be removed with the Chocolatey Uninstall
Install-ChocolateyPath $targetDir\jdk-$version\bin -PathType 'Machine'
