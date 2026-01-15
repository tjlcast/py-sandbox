docker rm -f py-sandbox
docker run -itd --name py-sandbox -p 8000:8000 --memory=512m --cpus=1 py-sandbox:latest