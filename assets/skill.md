# Unity DSH 桥接

本技能通过 Unity 编辑器内的一个 HTTP 服务(默认 `127.0.0.1:8790`)让 DSH 直接指挥 Unity。

## 首次使用(装 Unity 侧插件)

把本技能目录下的 `UnityPlugin/Assets/Editor/DshBridge/DshBridge.cs` 复制到用户的 Unity 项目(或团结引擎项目)的 `Assets/Editor/` 下,然后打开该项目。插件随编辑器自动启动;Unity 菜单 `DshBridge → Status Window` 打开状态面板,浏览器 `http://127.0.0.1:8790` 是网页状态页。

## 客户端

本目录 `client/unity_client.py`(仅标准库)。Windows 用 `py`,其他平台 `python3`:

```bash
py <本目录>/client/unity_client.py ping
py <本目录>/client/unity_client.py create_primitive '{"type":"cube","name":"Floor","scale":[10,1,10]}'
```

Python 内 `import unity_client as u; u.call("create_primitive", {...})`。

## 命令速查

- 场景: `new_scene` `hierarchy` `find` `create_primitive` `create_empty` `destroy` `set_transform` `set_active`
- 组件/属性: `add_component` `remove_component` `get_components` `set_property` `get_property`(反射,支持 `material.color` 嵌套、Vector3/Color 数组)
- 脚本/文件: `write_script`(路径须 `Assets/` 开头) `read_file` `list_dir`
- 编译: `compile` `compile_status`(errors/warnings 来自 Console)
- 运行: `playmode`(`enter`/`exit`) `playmode_state` `console`
- 调试/驱动: `invoke_static`(调任意静态方法) `screenshot` `create_material` `set_status`
- 资源: `save_scene` `open_scene` `quit`

## 闭环工作流(边看边调)

1. `screenshot` 截图,视觉模型用 read_image 看效果(无视觉则用结构化状态)。
2. `hierarchy` / `console` / `compile_status` 读结构与报错。
3. `write_script` 写 C# → `compile` → 等 `compile_status` 的 `compiling=false` → 读 `errors` 修正。
4. `set_property` / `add_component` / `invoke_static` 改内容。
5. `playmode enter` → 截图/读运行时字段 → 满意后 `playmode exit` + `save_scene`。

## 注意

- `ping` 返回 `changing:true` 表示正在域重载/进出 Play Mode,`compiling:true` 表示编译中,都要等它变 `false`。
- 编译或进出 Play Mode 会域重载,服务短暂重启(几秒),客户端要重试。
- 所有 Unity API 在主线程执行,阻塞超时 60 秒。
- `screenshot` 返回 `path`,用 `GET /file?path=...` 或 `unity_client.get_file(path, out)` 取图。
