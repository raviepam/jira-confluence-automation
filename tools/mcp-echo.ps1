$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$supportedProtocolVersion = "2025-06-18"

function Send-JsonRpcMessage {
    param([System.Collections.IDictionary] $Message)

    $json = ConvertTo-Json -InputObject $Message -Depth 32 -Compress
    [Console]::Out.WriteLine($json)
    [Console]::Out.Flush()
}

function Send-JsonRpcError {
    param(
        [object] $RequestId,
        [int] $Code,
        [string] $Message
    )

    Send-JsonRpcMessage @{
        jsonrpc = "2.0"
        id      = $RequestId
        error   = @{
            code    = $Code
            message = $Message
        }
    }
}

while ($null -ne ($line = [Console]::In.ReadLine())) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    try {
        $request = ConvertFrom-Json -InputObject $line -AsHashtable -NoEnumerate -ErrorAction Stop
    }
    catch {
        [Console]::Error.WriteLine("Ignoring invalid JSON-RPC input: $($_.Exception.Message)")
        continue
    }

    if ($request -isnot [System.Collections.IDictionary] -or -not $request.Contains("method")) {
        [Console]::Error.WriteLine("Ignoring input without a JSON-RPC method.")
        continue
    }

    $method = [string] $request["method"]
    $hasRequestId = $request.Contains("id")
    $requestId = $request["id"]
    $parameters = $request["params"]

    if (-not $hasRequestId) {
        if ($method -eq "notifications/exit") {
            break
        }
        continue
    }

    switch ($method) {
        "initialize" {
            $requestedVersion = $parameters["protocolVersion"]
            $negotiatedVersion = $supportedProtocolVersion
            if ($requestedVersion -eq $supportedProtocolVersion) {
                $negotiatedVersion = $requestedVersion
            }

            Send-JsonRpcMessage @{
                jsonrpc = "2.0"
                id      = $requestId
                result  = @{
                    protocolVersion = $negotiatedVersion
                    capabilities    = @{
                        tools = @{
                            listChanged = $false
                        }
                    }
                    serverInfo      = @{
                        name    = "hello-genai-powershell-echo"
                        version = "1.0.0"
                    }
                }
            }
            continue
        }

        "ping" {
            Send-JsonRpcMessage @{
                jsonrpc = "2.0"
                id      = $requestId
                result  = @{}
            }
            continue
        }

        "tools/list" {
            Send-JsonRpcMessage @{
                jsonrpc = "2.0"
                id      = $requestId
                result  = @{
                    tools = @(
                        @{
                            name        = "echo"
                            description = "Return the supplied text unchanged."
                            inputSchema = @{
                                type                 = "object"
                                properties           = @{
                                    message = @{
                                        type        = "string"
                                        description = "Text to echo back."
                                    }
                                }
                                required             = @("message")
                                additionalProperties = $false
                            }
                        }
                    )
                }
            }
            continue
        }

        "tools/call" {
            if ($parameters -isnot [System.Collections.IDictionary]) {
                Send-JsonRpcError -RequestId $requestId -Code -32602 -Message "Tool call parameters must be an object."
                continue
            }
            if ($parameters["name"] -ne "echo") {
                Send-JsonRpcError -RequestId $requestId -Code -32602 -Message "Unknown tool. Available tool: echo."
                continue
            }

            $arguments = $parameters["arguments"]
            if ($arguments -isnot [System.Collections.IDictionary] -or $arguments["message"] -isnot [string]) {
                Send-JsonRpcMessage @{
                    jsonrpc = "2.0"
                    id      = $requestId
                    result  = @{
                        content = @(
                            @{
                                type = "text"
                                text = "Invalid arguments: provide a string message."
                            }
                        )
                        isError = $true
                    }
                }
                continue
            }

            Send-JsonRpcMessage @{
                jsonrpc = "2.0"
                id      = $requestId
                result  = @{
                    content = @(
                        @{
                            type = "text"
                            text = $arguments["message"]
                        }
                    )
                    isError = $false
                }
            }
            continue
        }

        default {
            Send-JsonRpcError -RequestId $requestId -Code -32601 -Message "Method not found: $method"
        }
    }
}