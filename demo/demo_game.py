#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端演示:DSH 直接控制 Unity 完成一次"自动写游戏"循环。

流程:等 Unity -> 新建场景 -> 搭场景(地板/球/柱子) -> 建材质 ->
     写脚本(故意带错) -> 编译抓到报错 -> 修复 -> 编译通过 ->
     挂组件调参数 -> 写相机环绕脚本 -> 编辑态截图 -> 进 Play Mode 截图 -> 保存场景
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client"))
import unity_client as u

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))


def step(msg):
    u.try_call("set_status", {"text": msg}, timeout=5)
    print("\n=== %s ===" % msg, flush=True)


def main():
    step("1. 等待 Unity 与桥接服务启动(首次导入可能较久)")
    info = u.ping_until(timeout=900, verbose=True)
    print(json.dumps(info, ensure_ascii=False))

    step("2. 等待初始编译完成")
    u.wait_compile_idle(timeout=600)

    step("3. 新建场景")
    print(json.dumps(u.call("new_scene"), ensure_ascii=False))

    step("4. 搭建场景:地板 + 球 + 四根柱子")
    floor = u.call("create_primitive", {"type": "cube", "name": "Floor", "position": [0, -0.5, 0], "scale": [12, 1, 12]})
    ball = u.call("create_primitive", {"type": "sphere", "name": "Ball", "position": [0, 2, 0]})
    pillars = []
    for i, (x, z) in enumerate([(-5, -5), (5, -5), (-5, 5), (5, 5)]):
        pillars.append(u.call("create_primitive", {
            "type": "cube", "name": "Pillar%d" % i,
            "position": [x, 1, z], "scale": [0.6, 2, 0.6],
        }))
    print("floor:", json.dumps(floor, ensure_ascii=False))
    print("ball:", json.dumps(ball, ensure_ascii=False))

    step("5. 创建材质并赋给渲染器")
    u.call("create_material", {"name": "FloorMat", "color": [0.24, 0.27, 0.34, 1]})
    u.call("create_material", {"name": "BallMat", "color": [0.92, 0.22, 0.22, 1]})
    u.call("create_material", {"name": "PillarMat", "color": [0.85, 0.65, 0.2, 1]})
    u.call("set_property", {"target": "Floor", "component": "UnityEngine.MeshRenderer", "path": "sharedMaterial", "value": {"name": "FloorMat"}})
    u.call("set_property", {"target": "Ball", "component": "UnityEngine.MeshRenderer", "path": "sharedMaterial", "value": {"name": "BallMat"}})
    for i in range(4):
        u.call("set_property", {"target": "Pillar%d" % i, "component": "UnityEngine.MeshRenderer", "path": "sharedMaterial", "value": {"name": "PillarMat"}})
    print("materials ok")

    step("6. 写第一个游戏脚本(故意带一个编译错误),验证报错反馈闭环")
    buggy = r'''using UnityEngine;
public class HoverBall : MonoBehaviour
{
    public float speed = 60f;
    public float bobHeight = 0.5f;
    public float sway = 1.5f;
    private Vector3 start;
    void Start() { start = transform.position; }
    void Update()
    {
        transform.Rotate(0f, speed * Time.deltaTime, 0f);
        Vector3 p = start;
        p.y = start.y + Mathf.Sinn(Time.time * 2f) * bobHeight; // 故意写错: Mathf.Sinn 不存在
        p.x = start.x + Mathf.Sin(Time.time * 1.3f) * sway;
        transform.position = p;
    }
}
'''
    u.call("write_script", {"path": "Assets/Scripts/HoverBall.cs", "content": buggy})
    u.call("compile")
    u.wait_compile_idle(timeout=300)
    st = u.call("compile_status")
    errs = st.get("errors", [])
    print("编译错误数:", len(errs))
    for e in errs:
        print("  error:", e.get("message"), "|", e.get("file"), "line", e.get("line"))
    assert len(errs) > 0, "预期能抓到编译错误,但没有 -> 报错反馈链路有问题"

    step("7. 修复脚本重新编译,验证错误消除")
    fixed = buggy.replace("Mathf.Sinn", "Mathf.Sin")
    u.call("write_script", {"path": "Assets/Scripts/HoverBall.cs", "content": fixed})
    u.call("compile")
    u.wait_compile_idle(timeout=300)
    st = u.call("compile_status")
    print("修复后错误数:", len(st.get("errors", [])), "警告数:", len(st.get("warnings", [])))
    assert len(st.get("errors", [])) == 0, "修复后仍有编译错误"

    step("8. 挂组件 + 调参数(反射设置字段)")
    print(json.dumps(u.call("add_component", {"target": "Ball", "type": "HoverBall"}), ensure_ascii=False))
    u.call("set_property", {"target": "Ball", "component": "HoverBall", "path": "speed", "value": 90})
    print("speed 已调为 90, 读取确认:", json.dumps(u.call("get_property", {"target": "Ball", "component": "HoverBall", "path": "speed"}), ensure_ascii=False))

    step("9. 写相机环绕脚本并挂到 Main Camera")
    orbit = r'''using UnityEngine;
public class CameraOrbit : MonoBehaviour
{
    public float radius = 9f;
    public float height = 4f;
    public float speed = 20f;
    void Update()
    {
        float a = Time.time * speed * Mathf.Deg2Rad;
        transform.position = new Vector3(Mathf.Sin(a) * radius, height, Mathf.Cos(a) * radius);
        transform.LookAt(new Vector3(0f, 1f, 0f));
    }
}
'''
    u.call("write_script", {"path": "Assets/Scripts/CameraOrbit.cs", "content": orbit})
    u.call("compile")
    u.wait_compile_idle(timeout=300)
    st = u.call("compile_status")
    print("CameraOrbit 编译错误数:", len(st.get("errors", [])))
    assert len(st.get("errors", [])) == 0
    u.call("add_component", {"target": "Main Camera", "type": "CameraOrbit"})

    step("10. 编辑模式截图(场景验收)")
    shot = u.call("screenshot", {"width": 800, "height": 600, "position": [0, 4, -9], "lookAt": [0, 1.2, 0]})
    edit_png = os.path.join(DEMO_DIR, "shot_edit.png")
    u.get_file(shot["path"], edit_png)
    print("编辑模式截图:", edit_png, "|", shot["bytes"], "bytes")

    step("11. 进入 Play Mode 试玩并连拍两张")
    print(json.dumps(u.try_call("playmode", {"action": "enter"}), ensure_ascii=False))
    u.ping_until(timeout=180, verbose=False)  # 域重载后等服务回来
    time.sleep(3.0)
    s2 = u.call("screenshot", {"width": 800, "height": 600})
    play_png1 = os.path.join(DEMO_DIR, "shot_play_1.png")
    u.get_file(s2["path"], play_png1)
    time.sleep(0.8)
    s3 = u.call("screenshot", {"width": 800, "height": 600})
    play_png2 = os.path.join(DEMO_DIR, "shot_play_2.png")
    u.get_file(s3["path"], play_png2)
    print(json.dumps(u.try_call("playmode", {"action": "exit"}), ensure_ascii=False))
    u.ping_until(timeout=180, verbose=False)

    step("12. 保存场景,导出最终层级")
    print(json.dumps(u.call("save_scene", {"path": "Assets/Scenes/DemoGame.unity"}), ensure_ascii=False))
    hier = u.call("hierarchy")
    with open(os.path.join(DEMO_DIR, "result.json"), "w", encoding="utf-8") as f:
        json.dump(hier, f, ensure_ascii=False, indent=2)
    print(json.dumps(hier, ensure_ascii=False)[:600])

    print("\n=== DEMO OK ===")
    print("截图: %s\n      %s\n      %s" % (edit_png, play_png1, play_png2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n=== DEMO FAILED: %s ===" % e, file=sys.stderr)
        sys.exit(1)
