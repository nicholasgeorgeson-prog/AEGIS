<#
.SYNOPSIS
    TechWriterReview Hyperlink Validator v1.0
    
.DESCRIPTION
    Validates URLs from an input file and returns JSON results.
    Designed for air-gapped Windows environments where Python requests
    module may not be available.
    
    Output Statuses:
    - WORKING: URL returned HTTP 200
    - BROKEN: URL returned 4xx/5xx or connection failed
    - REDIRECT: URL returned 3xx redirect
    - TIMEOUT: Connection timed out
    - BLOCKED: Access denied or filtered (403, connection refused)
    - DNSFAILED: Could not resolve hostname
    - SSLERROR: SSL/TLS certificate error
    - UNKNOWN: Could not determine status
    
.PARAMETER InputFile
    Path to text file containing URLs (one per line)
    
.PARAMETER Urls
    Comma-separated list of URLs to validate (alternative to InputFile)
    
.PARAMETER OutputFormat
    Output format: JSON (default) or CSV
    
.PARAMETER TimeoutSeconds
    Timeout per URL in seconds (default: 10)
    
.PARAMETER FollowRedirects
    Follow HTTP redirects (default: true)
    
.PARAMETER MaxRedirects
    Maximum redirects to follow (default: 5)
    
.EXAMPLE
    .\HyperlinkValidator.ps1 -InputFile urls.txt -OutputFormat JSON
    
.EXAMPLE
    .\HyperlinkValidator.ps1 -Urls "https://google.com,https://example.com"
    
.NOTES
    Version: 1.0.0
    For TechWriterReview v3.0.37+
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$false)]
    [string]$Urls,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("JSON", "CSV")]
    [string]$OutputFormat = "JSON",
    
    [Parameter(Mandatory=$false)]
    [int]$TimeoutSeconds = 10,
    
    [Parameter(Mandatory=$false)]
    [bool]$FollowRedirects = $true,
    
    [Parameter(Mandatory=$false)]
    [int]$MaxRedirects = 5
)

$ErrorActionPreference = "SilentlyContinue"

# =============================================================================
# URL VALIDATION FUNCTION
# =============================================================================

function Test-UrlStatus {
    param(
        [string]$Url,
        [int]$Timeout = 10,
        [bool]$FollowRedirects = $true,
        [int]$MaxRedirects = 5
    )
    
    $result = @{
        url = $Url
        status = "UNKNOWN"
        statusCode = $null
        message = ""
        redirectUrl = $null
        redirectCount = 0
        responseTimeMs = $null
        checkedAt = (Get-Date).ToString("o")
    }
    
    # Validate URL format first
    try {
        $uri = [System.Uri]::new($Url)
        if ($uri.Scheme -notin @("http", "https")) {
            $result.status = "INVALID"
            $result.message = "Unsupported scheme: $($uri.Scheme)"
            return $result
        }
    }
    catch {
        $result.status = "INVALID"
        $result.message = "Invalid URL format: $_"
        return $result
    }
    
    # DNS Resolution check
    try {
        $hostname = $uri.Host
        $dnsResult = [System.Net.Dns]::GetHostAddresses($hostname)
        if (-not $dnsResult -or $dnsResult.Count -eq 0) {
            $result.status = "DNSFAILED"
            $result.message = "DNS resolution failed for $hostname"
            return $result
        }
    }
    catch {
        $result.status = "DNSFAILED"
        $result.message = "DNS lookup failed: $_"
        return $result
    }
    
    # HTTP Request
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        # Create HTTP request
        $request = [System.Net.HttpWebRequest]::Create($Url)
        $request.Method = "HEAD"
        $request.Timeout = $Timeout * 1000
        $request.AllowAutoRedirect = $FollowRedirects
        $request.MaximumAutomaticRedirections = $MaxRedirects
        $request.UserAgent = "TechWriterReview/3.0.37 HyperlinkValidator/1.0"
        
        # SSL/TLS handling
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 -bor [System.Net.SecurityProtocolType]::Tls11 -bor [System.Net.SecurityProtocolType]::Tls
        
        # Make request
        $response = $request.GetResponse()
        $stopwatch.Stop()
        
        $result.statusCode = [int]$response.StatusCode
        $result.responseTimeMs = $stopwatch.ElapsedMilliseconds
        
        # Check for redirects
        if ($response.ResponseUri.AbsoluteUri -ne $Url) {
            $result.redirectUrl = $response.ResponseUri.AbsoluteUri
            $result.redirectCount = 1  # Approximate - .NET doesn't expose redirect chain
        }
        
        # Map status code to status
        switch ([int]$response.StatusCode) {
            200 { 
                $result.status = "WORKING"
                $result.message = "OK"
            }
            { $_ -ge 300 -and $_ -lt 400 } {
                $result.status = "REDIRECT"
                $result.message = "Redirect to $($response.ResponseUri)"
            }
            default {
                $result.status = "WORKING"
                $result.message = "HTTP $($response.StatusCode)"
            }
        }
        
        $response.Close()
    }
    catch [System.Net.WebException] {
        $stopwatch.Stop()
        $result.responseTimeMs = $stopwatch.ElapsedMilliseconds
        
        $webEx = $_.Exception
        
        if ($webEx.Status -eq [System.Net.WebExceptionStatus]::Timeout) {
            $result.status = "TIMEOUT"
            $result.message = "Connection timed out after ${Timeout}s"
        }
        elseif ($webEx.Status -eq [System.Net.WebExceptionStatus]::NameResolutionFailure) {
            $result.status = "DNSFAILED"
            $result.message = "Could not resolve hostname"
        }
        elseif ($webEx.Status -eq [System.Net.WebExceptionStatus]::TrustFailure -or 
                $webEx.Status -eq [System.Net.WebExceptionStatus]::SecureChannelFailure) {
            $result.status = "SSLERROR"
            $result.message = "SSL/TLS certificate error: $($webEx.Message)"
        }
        elseif ($webEx.Status -eq [System.Net.WebExceptionStatus]::ConnectFailure) {
            $result.status = "BLOCKED"
            $result.message = "Connection refused or blocked"
        }
        elseif ($webEx.Response) {
            # We got an HTTP response (4xx, 5xx)
            $errorResponse = $webEx.Response
            $result.statusCode = [int]$errorResponse.StatusCode
            
            switch ([int]$errorResponse.StatusCode) {
                403 {
                    $result.status = "BLOCKED"
                    $result.message = "Access forbidden (403)"
                }
                404 {
                    $result.status = "BROKEN"
                    $result.message = "Page not found (404)"
                }
                { $_ -ge 400 -and $_ -lt 500 } {
                    $result.status = "BROKEN"
                    $result.message = "Client error: HTTP $_"
                }
                { $_ -ge 500 } {
                    $result.status = "BROKEN"
                    $result.message = "Server error: HTTP $_"
                }
                default {
                    $result.status = "UNKNOWN"
                    $result.message = "HTTP $_"
                }
            }
            $errorResponse.Close()
        }
        else {
            $result.status = "BROKEN"
            $result.message = "Connection failed: $($webEx.Status)"
        }
    }
    catch {
        $stopwatch.Stop()
        $result.status = "UNKNOWN"
        $result.message = "Unexpected error: $_"
        $result.responseTimeMs = $stopwatch.ElapsedMilliseconds
    }
    
    return $result
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# Gather URLs to validate
$urlList = @()

if ($InputFile) {
    if (Test-Path $InputFile) {
        $urlList = Get-Content $InputFile | Where-Object { $_.Trim() -ne "" }
    }
    else {
        Write-Error "Input file not found: $InputFile"
        exit 1
    }
}
elseif ($Urls) {
    $urlList = $Urls -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
}
else {
    # Read from stdin if no arguments
    $urlList = @($input) | Where-Object { $_.Trim() -ne "" }
}

if ($urlList.Count -eq 0) {
    Write-Error "No URLs provided. Use -InputFile, -Urls, or pipe URLs to stdin."
    exit 1
}

# Validate each URL
$results = @()
foreach ($url in $urlList) {
    $result = Test-UrlStatus -Url $url -Timeout $TimeoutSeconds -FollowRedirects $FollowRedirects -MaxRedirects $MaxRedirects
    $results += $result
}

# Output results
if ($OutputFormat -eq "JSON") {
    $results | ConvertTo-Json -Depth 10
}
else {
    # CSV output
    $results | Select-Object url, status, statusCode, message, redirectUrl, redirectCount, responseTimeMs, checkedAt | 
        ConvertTo-Csv -NoTypeInformation
}
