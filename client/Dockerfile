FROM python:3.6.1

WORKDIR /Users/Darragh/College/ScalableComputing/py_dfs/distibuted-file-system/client/
ADD . /Users/Darragh/College/ScalableComputing/py_dfs/distibuted-file-system/client/

# add requirements (to leverage Docker cache)
ADD ./requirements.txt requirements.txt

# install requirements
RUN pip install -r requirements.txt

# add app
ADD client.py /

# run server
# run server
CMD python client.py