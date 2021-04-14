FROM centos:latest
RUN groupadd -r noroot && useradd -r -g noroot noroot
USER noroot
RUN sudo yum install -y bash wget curl libGL zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel  libffi-devel gcc make \
&& wget https://www.python.org/ftp/python/3.7.9/Python-3.7.10.tgz \
&& tar -zxvf Python-3.7.10.tgz \
&& rm -rf Python-3.7.10.tgz \
&& cd Python-3.7.10 \
&& mkdir -p /usr/local/python3 \
&& ./configure \
&& make \
&&  make install \
&& ln -s /usr/local/bin/python3 /usr/bin/python3 \
&& ln -s /usr/local/bin/pip3 /usr/bin/pip3 \
&& pip3 install pyclipper Shapely onnxruntime opencv_python numpy Pillow tornado pycorrector jieba pypinyin six \
