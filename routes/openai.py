import http.server
import json
from typing import Any, Dict, Optional

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
            chunk_dict = chunk.to_dict()
            data_str = json.dumps(chunk_dict)

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
    finally:
        # Send final sentinel so clients know stream is complete and flush.
        try:
            request.wfile.write(b"data: [DONE]\n\n")
            request.wfile.flush()
        except Exception:
            pass

def models(request: http.server.BaseHTTPRequestHandler) -> Dict[str,Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": 1677610602,
                "owned_by": "ai-proxy",
            }
            for model_id in config.config.models()
        ],
    }

def model(model_id: str, _: http.server.BaseHTTPRequestHandler) -> Optional[Dict[str,Any]]:
    models = config.config.models()
    if model_id not in models:
        return None
    
    return {
        "id": model_id,
        "object": "model",
        "created": 1677610602,
        "owned_by": "ai-proxy",
    }