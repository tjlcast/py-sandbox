docker build --no-cache -t  py-sandbox .

docker run -itd -p 8000:8000 --name py-sandbox py-sandbox 
