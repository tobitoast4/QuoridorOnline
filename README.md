# QuoridorOnline

## Introduction

This repository conatins an online version of the game Quoridor.
The game can be played on a single PC as well as online n multiple (up to 4 players) without any registration needed.
See [website](https://quoridoronline.pythonanywhere.com/).


## Run the app locally

1. Install the requirements `pip install -r requirements.txt`
2. Run `/app.py`

## Run with gunicorn

`gunicorn -w 4 'app:app' -b 0.0.0.0:443 --certfile=/root/certs/ssl_cert.cer --keyfile=/root/certs/private_key.key --ca-certs=/etc/ssl/certs/ca-certificates.crt` 