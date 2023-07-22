FROM python:3.11-alpine
RUN python3 -m pip --no-cache-dir install markdown matrix-nio
ADD matrixchat-notify.py /bin/
ADD matrixchat-notify-config.json /etc/
RUN chmod +x /bin/matrixchat-notify.py
ENTRYPOINT ["/bin/matrixchat-notify.py", "-c", "/etc/matrixchat-notify-config.json"]
