FROM python:3.6.1

WORKDIR /Users/Darragh/College/ScalableComputing/py_dfs/distibuted-file-system/file-server/
ADD . /Users/Darragh/College/ScalableComputing/py_dfs/distibuted-file-system/file-server/

# add requirements (to leverage Docker cache)
ADD ./requirements.txt requirements.txt

# install requirements
RUN pip install -r requirements.txt

# add app
ADD file_server.py /

# run server
CMD [ "python3", "-u", "file_server.py" ]