docker rm -f py-sandbox
docker run -itd --name py-sandbox -p 8001:8000 --memory=512m --cpus=1 py-sandbox:latest
docker logs -f --tail 100 py-sandbox