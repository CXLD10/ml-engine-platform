.PHONY: run train test docker-build docker-run

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

train:
	python train.py --config configs/train.yaml

test:
	pytest -q

docker-build:
	docker build -t ml-engine-platform:phase4 .

docker-run:
	docker run --rm -p 8000:8000 --env-file .env -v $(PWD)/artifacts:/app/artifacts ml-engine-platform:phase4
