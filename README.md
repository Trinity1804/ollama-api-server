# Ollama API Server

A FastAPI-based server providing OpenAI-compatible API endpoints for Ollama models. You can run this on a server or locally, and make API requests to it from a client machine. The AI response will be streamed by default.

## Features

- OpenAI API-compatible endpoints
- Chat completions with streaming support
- API key authentication

## Requirements

- FastAPI
- Ollama
- Python 3.8+
- Uvicorn

## Quick Start

```bash
# Clone repository
git clone https://github.com/Trinity1804/ollama-api-server.git
cd ollama-api-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn ollama python-dotenv
```

### In case you want to run this on an external server:

```bash
ssh username@your_server_ip
```

Update packages on your server:

```bash
sudo apt update
```

Install Ollama:

```bash
snap install ollama
```

Install required python packages:

```bash
sudo apt install python3-pip python3-venv -y
cd /home/your_user/
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn ollama
```

Create a systemd service for uvicorn:

```bash
sudo vim /etc/systemd/system/uvicorn.service
```

Paste these as the contents:

```bash
[Unit]
Description=Uvicorn FastAPI Service
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/home/your_user/
Environment="OPENAI_API_KEY=your-api-key-here"
Environment="PATH=/home/your_user/venv/bin"
ExecStart=/home/your_user/venv/bin/uvicorn api-server:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

Start and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start uvicorn
sudo systemctl enable uvicorn
```

Allow port 8000 on the firewall

```bash
sudo ufw allow 8000
sudo ufw enable
```

## Environment Setup

```bash
# Create .env file
echo "OPENAI_API_KEY=your-secret-key-here" > .env
```

You can have any string here and treat that as an API key. It does not necessarily have to be an OpenAI API key.

## Usage

Install preferred model from Ollama:

```bash
ollama pull [model name here]
```

If you followed the instructions to run this on an external server, you can skip the following command as uvicorn will already be running.

To start the server, run:

```bash
uvicorn api-server:app --host 0.0.0.0 --port 8000
```

Example request:

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-api-key" \
     -d '{
       "model": "deepseek-r1:8b",
       "messages": [
         {
           "role": "user",
           "content": "Hello!"
         }
       ]
     }'
```

If you are running this on an external server, replace localhost with the address of your server.

## API Reference

`POST /v1/chat/completions`

Parameters:

* `model` (string): Ollama model name
* `messages` (array): Conversation messages

Response format:

```bash
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677858242,
  "model": "deepseek-r1:8b",
  "usage": {
    "prompt_tokens": 13,
    "completion_tokens": 7,
    "total_tokens": 20
  },
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Response content"
      },
      "finish_reason": "stop",
      "index": 0
    }
  ]
}
```
