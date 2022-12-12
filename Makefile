run_server:
	uvicorn server:app --reload --port 8002

install_requirements:
	pip3 install -r requirements.txt