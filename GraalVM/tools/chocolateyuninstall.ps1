$programFiles = (${env:ProgramFiles}, ${env:ProgramFiles(x86)} -ne $null)[0]
$installDir = "$programFiles\GraalVM"
$graalvmDir = "graalvm-community-openjdk-25.0.2+10.1"

Uninstall-ChocolateyEnvironmentVariable 'JAVA_HOME' 'Machine'
rm -r "$installDir\$graalvmDir"

$pathToUnInstall = "$installDir\$graalvmDir\bin"
$pathType = 'Machine'

$statementTerminator = ";"

$actualPath = [System.Collections.ArrayList](Get-EnvironmentVariable -Name 'Path' -Scope 'Machine' -PreserveVariables).split($statementTerminator)

if ($actualPath -contains $pathToUnInstall)
{
        Write-Host "PATH environment variable contains $pathToUnInstall. Removing..."

        $actualPath.Remove($pathToUnInstall)
        $newPath =  $actualPath -Join $statementTerminator

        $cmd = "Set-EnvironmentVariable -Name 'Path' -Value `'$newPath`' -Scope 'Machine'"

    if (Test-ProcessAdminRights) {
        Invoke-Expression $cmd
    } else {
        Start-ChocolateyProcessAsAdmin "$cmd"
    }
}

