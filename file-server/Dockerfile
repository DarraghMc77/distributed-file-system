FROM python:3.6.1

RUN mkdir -p /app/
WORKDIR /app/

# add requirements (to leverage Docker cache)
ADD ./requirements.txt /app/

# install requirements
RUN pip install -r requirements.txt

# add app
ADD . /app/
# run server
CMD [ "python3", "-u", "file_server.py" ]