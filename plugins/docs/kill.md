# 退出

要退出 wukong-robot ，根据当前情况的不同有不同的方式：

## 如果 wukong-robot 正在前台工作

可以直接按组合键 `Ctrl+4` 或 `Ctrl+\` 即可。在 Mac 系统下可能会弹出诸如 “Python 已停止工作” 的警告，仅仅只是系统的提示，不必理会。

## 如果 wukong-robot 正在后台工作

可以执行如下命令：

``` bash
ps auwx | grep wukong  # 查看wukong的PID号
kill -9 PID号
```

Linux 基础比较弱，不知道这个 `PID` 号怎么看，不知道啥是前台啥是后台的朋友：

1. 看我[这篇 issue 的回答](https://github.com/wzpan/wukong-robot/issues/11#issuecomment-464481848)；
2. 好好学习 Linux 。
