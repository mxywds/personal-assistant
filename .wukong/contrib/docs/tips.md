# wukong-robot 使用技巧

## 1. 提升 snowboy 唤醒成功率和准确度

wukong-robot 自带的唤醒词是 snowboy.umdl 通用模型（umdl）。如果在你的设备上无法唤醒成功，则可以考虑在当前设备上训练个人模型（pmdl）。

!> 通用模型是 snowboy 根据上千人的样本预训练好的模型，普适性较好。而个人模型只适用于个人使用，换一个人效果就会比较差。请根据需求来选择。预训练的通用模型可以在[这里](https://github.com/Kitt-AI/snowboy/tree/master/resources/models)下载。

在运行 wukong-robot 的机器上访问 [唤醒词训练站点](https://snowboy.hahack.com)，训练一下唤醒词。详见 [安装教程-更新唤醒词](/install?id=_6-%e6%9b%b4%e6%96%b0%e5%94%a4%e9%86%92%e8%af%8d%ef%bc%88%e5%8f%af%e9%80%89%ef%bc%8c%e6%a0%91%e8%8e%93%e6%b4%be%e5%bf%85%e9%a1%bb%ef%bc%89) 。

另外，如果出现经常误唤醒 wukong-robot ，可以尝试在配置文件中将 `sensitivity` 调低。

## 2. 修改唤醒词

### 2.1 修改 snowboy 的唤醒词

1. 访问唤醒词训练服务 https://snowboy.hahack.com ；
2. 训练你自己的模型；
3. 下载 pmdl 模型并放到 ~/.wukong 中；
4. 修改 config.yml 的 `model` 配置，改为你训练好的模型的文件名。

注意务必在 wukong-robot 所运行的同一设备上录制语音和训练唤醒词。由于不同的设备声卡的参数不同，在 A 机器上录制出来的语音训练成唤醒词后，放到 B 机器上使用效果可能会有很大差异。

### 2.2 修改 porcupine 的唤醒词

1. 到 [Picovoice Console](https://console.picovoice.ai/) 上为你的平台训练你的唤醒词。
2. 完成后保存到 `~/.wukong` 目录中。
3. 修改 config.yml 中 `porcupine` 的 `keyword_paths` 配置，增加你训练好的模型的文件名。

``` yaml
# porcupine 离线唤醒
# 登录 https://console.picovoice.ai/
# 可以获取 access_key 和训练自己的唤醒词
porcupine: 
    keyword:
        - 'porcupine'
    keyword_paths:
        # spiderman.ppn 是我训练的唤醒词，
        # 我保存为 ~/.wukong/spiderman.ppn，
        # 然后在下面添加一项
        - 'spiderman.ppn'
    access_key: 'xxxxxxxxxxxxxxxxxxxxxxxxxx'
```

!> 注意：一旦使用了自定义的唤醒词，默认使用的 `porcupine` 唤醒词将不可使用。

## 3. 降低误唤醒

有些朋友抱怨在听歌的时候，wukong-robot 会自己误唤醒自己。有几种策略可以优化这个问题：

1. 适当调低唤醒敏感度；
2. 开启回声消除。

下面我将逐一介绍：

### 3.1：适当调低唤醒的敏感度

在配置文件（`$HOME/.wukong/config.yml`）中，修改如下配置：

``` yaml
# 热词唤醒机制
# 可选值：
# porcupine（推荐）
# snowboy
detector: snowboy
# 灵敏度
sensitivity: 0.5
```

其中，`sensitivity` 是离线唤醒的灵敏度。它与离线唤醒的成功率和误唤醒率有着直接的关系。如果调得太高，wukong-robot 可以很容易唤醒，但是被误唤醒的几率也会增大；如果调得太低，误唤醒率会大幅降低，但是也可能导致 wukong-robot 很难被唤醒。建议你根据实际情况调节这个参数到一个合适的值。

### 3.2：开启回声消除

声学回声消除（Acoustic Echo Cancellation，AEC）简单来讲就是想办法从麦克风录入的声音中消除掉音响的输出的声音。AEC 最初是为了解决 VoIP（网络电话）中这样一个问题：即A与B进行通话，A端有麦克风和扬声器分别用来采集A的声音和播放B的声音，B端有麦克风和扬声器分别用来采集B的声音和播放A的声音，很明显，由于声音传播的特性，A端的麦克风在采集A的声音的同时，也采集到了A端扬声器播放的来自B的声音，也就是A端采集到的声音是一个混合的声音，这个声音通过网络发给B时，B就不仅能听到A的声音，也能听见B前几秒自己的声音，这就是在B端听到了B自己的回声，同理在A端也可以听到A自己的回声，这显然不是我们想要的。

在 Linux 系统上，我们可以使用如下两种方式来实现回声消除：

1. 直接使用 PulseAudio 的 webrtc 回声消除模块。
2. 使用 [ec](https://github.com/voice-engine/ec) 。

#### 方法1. 使用 webrtc 回声消除模块（推荐）

编辑 `/etc/pulse/default.pa` 文件 最后加入

```
.ifexists module-echo-cancel.so
load-module module-echo-cancel aec_method=webrtc source_name=echocancel sink_name=echocancel1
set-default-source echocancel
set-default-sink echocancel1
.endif
```

#### 方法2. 使用 ec

首先安装 ec ：

``` bash
sudo apt-get -y install libasound2-dev libspeexdsp-dev
git clone https://github.com/voice-engine/ec.git
cd ec
make
cp ec /usr/local/bin/
```

然后根据你的板子是否带有硬件音频回路（hardware audio loopback），有不同的配置方案：

##### 不支持硬音频回路

普通的麦克风以及 respeaker 2 Mic HAT 不支持硬音频回路。所以我们需要使用软件的方式来进行回声消除。

可以写一个脚本来实现回声消除（请先确保已安装 pulseaudio ）：

``` bash
pacmd load-module module-pipe-sink sink_name=ec.sink format=s16 rate=16000 channels=1 file=/tmp/ec.input
pacmd load-module module-pipe-source source_name=ec.source format=s16 rate=16000 channels=2 file=/tmp/ec.output
pacmd set-default-sink ec.sink
pacmd set-default-source ec.source

ec -i plughw:0 -o plughw:0  # 编号请以实际为准！
```

如果是 respaker 2 Mic Hat，建议把上面的脚本最后一句改为：

``` bash
ec -i plughw:0 -o plughw:0 -d 200  # 编号请以实际为准！
```

注意以上的编号分别对应的是你的输入声卡和输出声卡的编号，请和 `.asoundrc` 里的配置保持一致。

将之保存为 `$HOME/start_ec.sh` 。在启动 wukong-robot 前，先执行这个脚本：

``` bash
sh start_ec.sh
```

此时先测试一下 `arecord`，`aplay` 是否正常工作，如果都没有问题，再启动 wukong-robot 。此时将可以看到 ec 有下面这样的输出：

``` bash
default pipe size: 65536
new pipe size: 8192
skip frames 200
Enable AEC
playback filled 1024 bytes zero
No playback, bypass AEC
```

说明回声消除已经启用。

##### 支持硬音频回路

可以使用 `ec_hw` 来实现回声消除，详见 [`ec_hw` for devices with hardware audio loopback](https://github.com/voice-engine/ec#ec_hw-for-devices-with-hardware-audio-loopback) 。

!> 如无必要尽量避免重启 `ec` 或 `ec_hw` ，否则可能会导致录音无法正常工作。如果遇到这个问题，可以重启设备解决。

## 4. 提升语音识别准确率

不同的厂商都提供了录入自己的词库以提升识别率的方案。以百度的 ASR 为例，可以将常用的指令、姓名等术语写成一个 command.txt 文件，然后登录您的百度语音应用管理页面，在 【自定义设置】 的 【语音识别词库设置】 项目中，点击 【进行设置】 按钮，上传该指令文件即可。文件内容示例：

```
音乐
下一首歌
下首歌
切歌
上一首歌
上首歌
停止
停止播放
暂停
暂停播放
重新播放
随机播放
单曲循环
大声
小声
大点声
小点声
大声点
小声点
歌单
榜单
几点
时间
邮件
邮箱
绕口令
笑话
搜索
别听我的
听我的
```

## 5. 在外网访问家中的 wukong-robot

有多种方案可以实现内网穿透，例如：

1. [frp](https://diannaobos.com/frp/)
2. [ngrok](https://ngrok.com/)
3. [花生棒](https://hsk.oray.com/device)

可以详细参考如下几篇文章：

* [可以实现内网穿透的几款工具](https://my.oschina.net/ZL520/blog/2086061)
* [内网穿透哪家好？端口映射/DDNS/花生壳/Ngrok/Frp 逐一介绍分析](https://www.zhihu.in/archives/237)
* [内网穿透的一点经验](https://sst.st/p/213)

## 6. 设置开机自启动

!> 以下方法仅在树莓派系统中测试通过，不保证在所有系统中可用。

1. 确保 tmux 已安装

``` bash
sudo apt-get install -y tmux
```

2. 在用户目录下创建一个 wukong-launcher.sh 脚本，内容为：

``` bash
#!/bin/bash
sleep 1

session_name=wukong

#Restore Configuration of AlsaMixer
if [ -f $HOME/asound.state ]; then
    alsactl --file=$HOME/asound.state restore
    sleep 1
fi

#Start wukong-robot
tmux new-session -d -s $session_name $HOME/wukong-robot/wukong.py
sleep 1

cd $HOME/wukong-robot
```

注意把脚本中的 `$HOME/wukong-robot` 改成你实际存放 wukong-robot 的位置。

3. 给这个脚本添加可执行权限：

``` bash
sudo chmod +x wukong-launcher.sh
```

4. 创建一个启动项文件到 `$HOME/.config/autostart` 中（如果不存在这个目录可以手动创建下），例如：

``` bash
touch $HOME/.config/autostart/wukong.desktop
```

5. 编辑这个 wukong.desktop ，粘贴如下内容：

``` bash
[Desktop Entry]
Name=wukong
Comment=wukong-robot
Exec=sh /home/pi/wukong-launcher.sh
Icon=/home/pi/python_games/4row_black.png
Terminal=false
MultipleArgs=false
Type=Application
Categories=Application;Development;
StartupNotify=true
```

注意把上述内容中的 `/home/pi` 改成你实际的用户目录地址。

完成后重启试试。

