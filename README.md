[![DSH Market 收录徽章](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-zh.svg)](https://dsh.market/?q=142gg-GZX%2Funity-dsh-bridge)

# unity-dsh-bridge

让 DeepSeek Harness(DSH)直接控制 Unity / 团结引擎(Tuanjie)编辑器:搭场景、写 C# 脚本、编译排错、进 Play Mode、截图、模拟输入,实现"边看效果边调试"的闭环。

一个项目同时是:**DSH 插件 bundle** + **Unity Editor 插件** + **Python 客户端**。

## 架构

```
DSH(agent)  ←HTTP JSON 127.0.0.1:8790→  Unity Editor 插件(DshBridge.cs)
   │                                        ├─ 场景/组件/材质/脚本
   │                                        ├─ 编译与报错捕获
   └── client/unity_client.py                ├─ Play Mode / 截图
                                             └─ 状态面板(编辑器窗口 + 网页)
```

## 安装方式(任选)

### A. 作为 DSH 插件安装(推荐)

```bash
# 直接从 GitHub 安装
dsh plugin --profile desktop add github:142gg-GZX/unity-dsh-bridge

# 或本地目录
dsh plugin --profile desktop add <本仓库路径>
```

装完重启 DSH,技能 `unity-dsh-bridge` 即出现在技能目录。

### B. 只装 Unity 侧插件(手动)

把 `assets/UnityPlugin/Assets/Editor/DshBridge/DshBridge.cs` 复制到任意 Unity 项目(Unity 2019.4+/2020.3/2022.3,或团结引擎)的 `Assets/Editor/` 下,打开项目即自动启动。菜单 `DshBridge → Status Window` 打开面板;浏览器 `http://127.0.0.1:8790` 看网页状态页。

### C. 只用 Python 客户端(不装 DSH 插件)

```bash
py client/unity_client.py ping
py client/unity_client.py create_primitive '{"type":"cube","name":"Floor","scale":[10,1,10]}'
```

## 命令速查

场景 `new_scene` `hierarchy` `find` `create_primitive` `create_empty` `destroy` `set_transform` `set_active`
组件 `add_component` `remove_component` `get_components` `set_property` `get_property`
脚本 `write_script` `read_file` `list_dir`
编译 `compile` `compile_status`
运行 `playmode` `playmode_state` `console`
调试 `invoke_static` `screenshot` `create_material` `set_status`
资源 `save_scene` `open_scene` `quit`

## 演示

```bash
py demo/demo_game.py     # 搭场景→写脚本(故意报错)→编译纠错→Play Mode→截图
py demo/demo_camera.py   # 写摄像机环绕脚本 + 搭场地
py demo/demo_input.py    # 按键控制相机 + AI 模拟输入
```

## 兼容性

- Unity 2019.4+ / 2020.3 / 2022.3,以及团结引擎(Tuanjie)2022.3。
- 团结引擎无 `CompilationPipeline.Get*Messages` API,插件已用 Console 日志报告编译错误。
- 服务仅监听 `127.0.0.1`,不暴露外网。

## License

MIT
