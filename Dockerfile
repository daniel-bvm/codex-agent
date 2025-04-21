from nikolasigmoid/py-agent-infra:latest

copy app app
copy requirements.txt requirements.txt
run python -m pip install --no-cache-dir -r requirements.txt

run curl -fsSL https://deb.nodesource.com/setup_23.x | bash - \
    && apt-get update \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @openai/codex

run apt-get update && apt-get install sudo -y 