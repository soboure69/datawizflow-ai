.PHONY: install run test docker demo

install:
	pip install -r requirements.txt

demo:
	python scripts/generate_demo_db.py

run:
	python -m streamlit run app.py

test:
	pytest -q

docker:
	docker compose up --build
