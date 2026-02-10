import http.server
import json
from typing import Any, Dict

from clients.openai import OpenAIClient
from openai.types.chat.chat_completion import ChatCompletion
import config

def handle500(request: http.server.BaseHTTPRequestHandler) -> None:
    request.send_response(500)
    request.send_header("Cache-Control", "no-cache")
    request.send_header("Content-Type", "application/json")
    request.end_headers()
    
    request.wfile.write(json.dumps({"error": "Internal server error"}).encode('utf-8'))

def handle(json_data : Dict[str,Any], request: http.server.BaseHTTPRequestHandler) -> None:
    ai_client = OpenAIClient(config.config.api_key(), config.config.base_url())
    response : ChatCompletion = ai_client.chat.completions.create(**json_data)

    stream = json_data.get("stream", False)

    if not stream:
        json_str = response.to_json()
        json_value = json.loads(json_str)
        result = json.dumps(json_value).encode('utf-8')

        request.send_response(200)
        request.send_header("Cache-Control", "no-cache")
        request.send_header("Content-Type", "application/json")
        request.end_headers()
        
        request.wfile.write(result)
        return
    
    # If stream is True, we need to handle the stream response differently
    request.send_response(200)
    request.send_header("Cache-Control", "no-cache")
    request.send_header("Content-Type", "text/event-stream")
    request.send_header("Connection", "keep-alive")
    request.end_headers()

    try:
        # The SDK may return an iterable streaming response. Handle several possible chunk types.
        for chunk in response:
            data_str = json.dumps(chunk)

            # Send as Server-Sent Events `data: <json>\n\n` so clients can stream-parse easily.
            payload = f"data: {data_str}\n\n".encode("utf-8")
            request.wfile.write(payload)
            request.wfile.flush()
    except Exception:
        # On any streaming error, attempt to close the connection gracefully.
        try:
            request.wfile.write(b"data: {\"error\": \"streaming error\"}\n\n")
            request.wfile.flush()
        except Exception:
            pass

def models(_,request: http.server.BaseHTTPRequestHandler) -> Dict[str,Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai",
            }
            for model_id in config.config.models()
        ],
    }