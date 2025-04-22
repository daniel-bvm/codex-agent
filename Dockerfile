from nikolasigmoid/py-agent-infra:latest

copy app app
copy requirements.txt requirements.txt
run python -m pip install --no-cache-dir -r requirements.txt

run curl -fsSL https://deb.nodesource.com/setup_23.x | bash - \
    && apt-get update \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

arg CACHEBUST=202504220452
run git clone --depth 1 https://github.com/TrustlessComputer/openai-codex.git anon-codex && \
    cd anon-codex && git pull

run cd anon-codex/codex-cli && npm install && npm run build

run apt-get update && apt-get install sudo -y 

env FORWARD_ALL_MESSAGES=1