import-module au
. $PSScriptRoot\..\_scripts\all.ps1

function global:au_SearchReplace {
   @{
        ".\tools\chocolateyInstall.ps1" = @{
			"(?i)(\s*url\s*=\s*)'.*'"     = "`${1}'$($Latest.URL32)'"
			"(?i)(\s*checksum\s*=\s*)'.*'"     = "`${1}'$($Latest.Checksum32)'"
			"(?i)(\s*checksumType\s*=\s*)'.*'" = "`${1}'$($Latest.ChecksumType32)'"
			"(?i)(\s*url64\s*=\s*)'.*'"     = "`${1}'$($Latest.URL64)'"
			"(?i)(\s*checksum64\s*=\s*)'.*'"     = "`${1}'$($Latest.Checksum64)'"
			"(?i)(\s*checksumType64\s*=\s*)'.*'" = "`${1}'$($Latest.ChecksumType64)'"
        }
    }
}

function global:au_BeforeUpdate { Get-RemoteFiles -Purge }

function global:au_GetLatest {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $download_page = Invoke-WebRequest https://www.freedownloadmanager.org/download.htm

	$version = ($download_page.AllElements | Where{$_.class -eq "version"}).innerText | Select-String -Pattern '\d+\.\d+\.\d+' | % { $_.Matches } | % { $_.Value }

	$url64   = $download_page.Links | Foreach {$_.href } | Select-String -Pattern 'fdm_x64_setup.exe' | ForEach-Object {$_ -Replace "\/\/", "https://"}
	$url   = $download_page.Links | Foreach {$_.href } | Select-String -Pattern 'fdm_x86_setup.exe' | ForEach-Object {$_ -Replace "\/\/", "https://"}

    @{
        Version      = $version
        URL32        = $url
        URL64        = $url64
    }
}

update -ChecksumFor all