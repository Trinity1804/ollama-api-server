from fastapi import FastAPI, Security, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from ollama import chat
from ollama import ChatResponse
import time
import os
import json
import asyncio

app = FastAPI()

API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)
EXPECTED_API_KEY = os.getenv("OPENAI_API_KEY")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: bool = False

class CompletionTokensDetails(BaseModel):
    reasoning_tokens: int
    accepted_prediction_tokens: int
    rejected_prediction_tokens: int

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    completion_tokens_details: CompletionTokensDetails

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str
    logprobs: Optional[dict] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    usage: Usage
    choices: List[Choice]

class ChatCompletionChunk(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]

def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key missing",
        )
    if api_key != f"Bearer {EXPECTED_API_KEY}":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return api_key

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatRequest, api_key: str = Security(verify_api_key)):
    if not request.stream:
        try:
            messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            response: ChatResponse = chat(model=request.model, messages=messages)
            
            assistant_content = response['message']['content']
            assistant_message = {
                "role": "assistant",
                "content": assistant_content
            }
            
            # Placeholder values for usage
            prompt_tokens = sum(len(msg['content'].split()) for msg in messages)
            completion_tokens = len(assistant_content.split())
            total_tokens = prompt_tokens + completion_tokens
            
            usage = Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                completion_tokens_details=CompletionTokensDetails(
                    reasoning_tokens=0,
                    accepted_prediction_tokens=0,
                    rejected_prediction_tokens=0
                )
            )
            
            choice = Choice(
                index=0,
                message=Message(**assistant_message),
                finish_reason="stop",
                logprobs=None
            )
            
            chatcompl = ChatCompletionResponse(
                id="chatcmpl-abc123",
                object="chat.completion",
                created=int(time.time()),
                model=request.model,
                usage=usage,
                choices=[choice]
            )
            print(chatcompl)
            return chatcompl
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )
    
    async def generate_chunks():
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        response = chat(
            model=request.model,
            messages=messages,
            stream=True
        )
        
        for chunk in response:
            if 'message' in chunk:
                content = chunk['message'].get('content', '')
                chunk_data = ChatCompletionChunk(
                    id=f"chatcmpl-{int(time.time())}",
                    object="chat.completion.chunk",
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        Choice(
                            index=0,
                            message=Message(role="assistant", content=content),
                            finish_reason=None if 'done' not in chunk else "stop"
                        )
                    ]
                )
                yield f"data: {json.dumps(chunk_data.dict())}\n\n"
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_chunks(),
        media_type="text/event-stream"
    )