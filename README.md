# personal-assistant

本地知识库+语音对话的个人助理 (基于[`wukong-robot`](./robot.md)魔改)

<!-- PROJECT SHIELDS -->

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<br />
<p align="center">

<h3 align="center">您的私人AI个人助理</h3>
  <p align="center">
    <a href="https://github.com/mxywds/personal-assistant/issues">报告Bug</a>
    ·
    <a href="https://github.com/mxywds/personal-assistant/issues">提出新特性</a>
  </p>
</p>

## 新增功能点
* 增加对百度大语言模型`ERNIE`的支持
* 增加对`ChatTTS`的支持


## 开发计划
1. [ ] 控制ChatTTS笑声停顿位置及多说话人
2. [ ] 完善技能能力（对外部api或设备的调用，指令切换音色，语言模型等）
3. [ ] 对话可打断
4. [ ] 加快应答速度
5. [ ] 重构web端
6. [ ] 知识库


## 环境要求
### Python 版本
personal-assistant 只支持 Python 3.7+，不支持 Python 2.x 。

### 设备要求
personal-assistant 支持运行在以下的设备和系统中：

* Intel Chip Mac (不支持苹果 M 系列芯片)
* 64bit Ubuntu（12.04 and 14.04）
* 全系列的树莓派（Raspbian 系统）
* Pine 64 with Debian Jessie 8.5（3.10.102）
* Intel Edison with Ubilinux （Debian Wheezy 7.8）
* 装有 WSL（Windows Subsystem for Linux） 的 Windows

### 手动安装
### 第一步
```shell
sudo apt-get update -y
sudo apt-get install portaudio19-dev python-pyaudio python3-pyaudio sox pulseaudio libsox-fmt-all ffmpeg
pip3 install pyaudio
```
### 第二步
```shell
cd personal-assistant
pip3 install -r requirements.txt
pip3 install -r .wukong/contrib/requirements.txt
```
### 第三步
#### 编译 _snowboydetect.so

安装 `swig`
首先确保你的系统已经装有 `swig` 。  
Linux 系统和带有WSL的win系统执行如下：

```shell
cd temp
wget https://wzpan-1253537070.cos.ap-guangzhou.myqcloud.com/misc/swig-3.0.10.tar.gz
tar xvf swig-3.0.10.tar.gz
cd swig-3.0.10
sudo apt-get -y update
sudo apt-get install -y libpcre3 libpcre3-dev
./configure --prefix=/usr --without-clisp --without-maximum-compile-warnings
make
sudo make install
sudo install -v -m755 -d /usr/share/doc/swig-3.0.10
sudo cp -v -R Doc/* /usr/share/doc/swig-3.0.10
sudo apt-get install -y libatlas-base-dev
```


构建 `snowboy`
```shell
wget https://wzpan-1253537070.cos.ap-guangzhou.myqcloud.com/wukong/snowboy.tar.bz2 # 使用我fork出来的版本以确保接口及Ubuntu 22兼容
tar -xvjf snowboy.tar.bz2
cd snowboy/swig/Python3
make
```
复制 `_snowboydetect.so`到项目的根目录的`snowboy`文件夹
```shell
cp _snowboydetect.so wukon-robot的根目录/snowboy/
```

运行
```shell
python3 wukong.py
```



### 常见问题
#### apt-get 或 pip 下载速度过慢
请自行换源

#### 唤醒词训练：
#### 二选一
#### snowboy：
1. 访问唤醒词训练服务 https://snowboy.hahack.com ；
2. 训练你自己的模型；
3. 下载 pmdl 模型并放到 ~/.wukong 中；
4. 修改 config.yml 的 model 配置，改为你训练好的模型的文件名。

#### porcupine：
1. 到 Picovoice Console 上为你的平台训练你的唤醒词。
2. 完成后保存到 ~/.wukong 目录中。
3. 修改 config.yml 中 porcupine 的 keyword_paths 配置，增加你训练好的模型的文件名。

#### No module named _snowboydetect
1. 使用 Python 3 执行本程序
2. 确保用上了平台可用的 _snowboydetect.so 包。(注意：WSL方式下，请不要直接运行在win系统，比如在编辑器直接跑就会报这个错误)

#### No such file or directory: 'play'
```sudo apt-get install sox ```


#### 离线唤醒机制初始化失败：[Errno -9996] Invalid input device (no default output device)
1. 启动了多个 personal-assistant 了。请kill 掉所有后台的 wukong 进程。
2. WSL方式下的声音问题：  
   请在此下载 pulseaudio：https://www.freedesktop.org/wiki/Software/PulseAudio/Ports/Windows/Support/  
   按照这篇文章配置：https://blog.csdn.net/jiexijihe945/article/details/131680406 和  
   https://martin1994.sinaapp.com/archives/916  
   文中的ip不要用127.0.0.1或者localhost

#### 提示音可以播放，但是tts没有声音
`sudo apt-get install libsox-fmt-mp3`

#### 其他问题
可参考原作者文档：[wukong-robot](https://wukong.hahack.com/#/README)  
原作者信息：
```
@misc{wukong-robot,
  author = {潘伟洲},
  title = {wukong-robot，一个简单、灵活、优雅的中文语音对话机器人/智能音箱项目},
  year = {2019},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/wzpan/wukong-robot}},
}
```

### 作者

ss.ok@foxmail.com

*您也可以在贡献者名单中参看所有参与该项目的开发者。*

### 版权说明

该项目签署了MIT 授权许可，详情请参阅 [LICENSE](https://github.com/mxywds/personal-assistant/blob/master/LICENSE.txt)

<!-- links -->
[your-project-path]:mxywds/personal-assistant

[contributors-shield]: https://img.shields.io/github/contributors/mxywds/personal-assistant.svg?style=flat-square

[contributors-url]: https://github.com/mxywds/personal-assistant/graphs/contributors

[forks-shield]: https://img.shields.io/github/forks/mxywds/personal-assistant.svg?style=flat-square

[forks-url]: https://github.com/mxywds/personal-assistant/network/members

[stars-shield]: https://img.shields.io/github/stars/mxywds/personal-assistant.svg?style=flat-square

[stars-url]: https://github.com/mxywds/personal-assistant/stargazers

[issues-shield]: https://img.shields.io/github/issues/mxywds/personal-assistant.svg?style=flat-square

[issues-url]: https://img.shields.io/github/issues/mxywds/personal-assistant.svg

[license-shield]: https://img.shields.io/github/license/mxywds/personal-assistant?style=flat-square

[license-url]: https://github.com/mxywds/personal-assistant/blob/master/LICENSE






