sudo apt update && sudo apt install -y python3-pip python3-venv
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn requests
python3 micro_saas_api.py
