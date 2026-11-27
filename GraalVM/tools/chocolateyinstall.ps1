$ErrorActionPreference = 'Stop'
$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\GraalVM"
$graalvmDir = "graalvm-community-25.6.5.1+2.1"

$packageArgs = @{
    PackageName = $env:ChocolateyPackageName
    UnzipLocation = $targetDir = $installDir
    Url64bit = 'https://github.com/graalvm/graalvm-ce-builds/releases/download/graal-25.6.5.1/graalvm-community-jdk-25i6-25.0.5.1_windows-x64_bin.zip'
    Checksum64 = '1f534c46337f838880553c47f973a3d769b4058036288afcec930e2abddf06a1'
    ChecksumType64 = 'sha256'
}

Install-ChocolateyZipPackage @packageArgs
Install-ChocolateyEnvironmentVariable 'JAVA_HOME' "$targetDir\$graalvmDir" 'Machine'
# The full path instead of the %JAVA_HOME% is needed so it can be removed with the Chocolatey Uninstall
Install-ChocolateyPath "$targetDir\$graalvmDir\bin" -PathType 'Machine'
