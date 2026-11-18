$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\OpenJDK"

$version = "27.0.1.1"

$packageArgs = @{
    PackageName      = $env:ChocolateyPackageName
    UnzipLocation    = $targetDir = $installDir
    Url64            = 'https://download.java.net/java/GA/jdk27.0.1.1/c3a705caf5044be8aa0b09e62be69b20/4/GPL/openjdk-27.0.1.1_windows-x64_bin.zip'
    Checksum64       = 'bbb09207b18730d2b4796904f24aa0527b7bc3fc2c59076f3f04af32baaaf8b6'
    ChecksumType64   = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyEnvironmentVariable 'JAVA_HOME' $targetDir\jdk-$version 'Machine'
# The full path instead of the %JAVA_HOME% is needed so it can be removed with the Chocolatey Uninstall
Install-ChocolateyPath $targetDir\jdk-$version\bin -PathType 'Machine'
