# 使用官方 Python 3.8 基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

## 使用镜像站点地址替换默认的包管理源
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main" > /etc/apt/sources.list \
    && echo "deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-updates main" >> /etc/apt/sources.list \
    && echo "deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-updates main" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-backports main" >> /etc/apt/sources.list \
    && echo "deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-backports main" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security buster/updates main" >> /etc/apt/sources.list \
    && echo "deb-src https://mirrors.tuna.tsinghua.edu.cn/debian-security buster/updates main" >> /etc/apt/sources.list \
    && apt-get clean


# 安装依赖库
RUN apt-get update && apt-get install -y \
    git \
    portaudio19-dev \
    python3-pyaudio \
    sox \
    pulseaudio \
    libsox-fmt-all \
    ffmpeg \
    wget \
    swig \
    libpcre3 \
    libpcre3-dev \
    libatlas-base-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 将项目文件夹中的所有内容复制到容器的 /app 目录中
COPY ../ /app

# 安装 PyAudio
RUN pip install pyaudio

# 安装 Python 依赖
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# 安装 contrib
RUN pip install -r .wukong/contrib/requirements.txt

# 下载并编译 snowboy
RUN wget https://wzpan-1253537070.cos.ap-guangzhou.myqcloud.com/misc/snowboy.tar.bz2 \
    && tar -xvjf snowboy.tar.bz2 \
    && cd snowboy/swig/Python3 \
    && make \
    && cp _snowboydetect.so /app/snowboy/

# 暴露端口
EXPOSE 5001

# 设置 ENTRYPOINT
ENTRYPOINT ["python", "wukong.py"]
