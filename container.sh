docker stop $(docker ps -a -q --filter ancestor="chatbot_ver-10-chatbot")
docker rmi -f chatbot_ver-10-chatbot:latest
docker compose up --build -d