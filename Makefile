SERVERS := 0 1 2 3 4 5

run-%:
	SERVER_ID=$* python server.py

run-all:
	for id in $(SERVERS); do \
		echo "Starting server $$id"; \
		SERVER_ID=$$id python server.py & \
	done
