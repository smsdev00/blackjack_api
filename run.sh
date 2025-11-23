bash

# start Redis
sudo systemctl start redis

# start backend
python main.py

# start html server
python -m http.server 8080

# Abre el HTML en el navegador
firefox http:127.0.0.1:8080
