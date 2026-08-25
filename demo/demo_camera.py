#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""现场写摄像机控制脚本 + 搭场地 + Play Mode 验证"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client"))
import unity_client as u

def step(msg):
    u.try_call("set_status", {"text": msg}, timeout=5)
    print(msg, flush=True)

CAMERA_SCRIPT = r'''using UnityEngine;

public class CameraController : MonoBehaviour
{
    public Transform target;
    public float distance = 10f;
    public float height = 4f;
    public float orbitSpeed = 20f;
    public float zoomSpeed = 6f;

    private float angle;

    void Update()
    {
        angle += orbitSpeed * Time.deltaTime;

        if (Input.GetKey(KeyCode.A)) angle -= orbitSpeed * 2.5f * Time.deltaTime;
        if (Input.GetKey(KeyCode.D)) angle += orbitSpeed * 2.5f * Time.deltaTime;
        if (Input.GetKey(KeyCode.Q)) height += 6f * Time.deltaTime;
        if (Input.GetKey(KeyCode.E)) height -= 6f * Time.deltaTime;

        float scroll = Input.GetAxis("Mouse ScrollWheel");
        distance = Mathf.Clamp(distance - scroll * zoomSpeed, 2f, 30f);

        Vector3 center = target != null ? target.position : Vector3.zero;
        float a = angle * Mathf.Deg2Rad;
        transform.position = center + new Vector3(Mathf.Sin(a) * distance, height, Mathf.Cos(a) * distance);
        transform.LookAt(center + Vector3.up * 1f);
    }
}
'''

def main():
    step("等待 Unity 桥接就绪")
    u.ping_until(timeout=600, verbose=False)

    step("确保不在播放模式")
    st = u.try_call("playmode_state")
    if st.get("playing") or st.get("changing"):
        u.try_call("playmode", {"action": "exit"})
        u.ping_until(timeout=120, verbose=False)
    u.wait_compile_idle(timeout=300, verbose=False)

    step("新建场景")
    u.call("new_scene")

    step("搭场地:地面+柱子+纪念碑+球")
    u.call("create_primitive", {"type": "cube", "name": "Ground", "position": [0, -0.25, 0], "scale": [20, 0.5, 20]})
    for i, (x, z) in enumerate([(-4, -4), (4, -4), (-4, 4), (4, 4)]):
        u.call("create_primitive", {"type": "cube", "name": "Pillar%d" % i, "position": [x, 1.5, z], "scale": [0.8, 3, 0.8]})
    u.call("create_primitive", {"type": "cylinder", "name": "Monument", "position": [0, 1, 0], "scale": [1, 2, 1]})
    u.call("create_primitive", {"type": "sphere", "name": "Orb", "position": [0, 2.6, 0], "scale": [0.5, 0.5, 0.5]})

    step("上材质")
    u.call("create_material", {"name": "GroundMat", "color": [0.22, 0.32, 0.24, 1]})
    u.call("create_material", {"name": "PillarMat", "color": [0.85, 0.65, 0.2, 1]})
    u.call("create_material", {"name": "MonumentMat", "color": [0.8, 0.2, 0.25, 1]})
    u.call("create_material", {"name": "OrbMat", "color": [0.25, 0.55, 0.95, 1]})
    u.call("set_property", {"target": "Ground", "component": "UnityEngine.MeshRenderer", "path": "sharedMaterial", "value": {"name": "GroundMat"}})
    for i in range(4):
        u.call("set_property", {"target": "Pillar%d" % i, "component": "UnityEngine.MeshRenderer", "path": "sharedMaterial", "value": {"name": "PillarMat"}})
    u.call("set_property", {"target": "Monument", "component": "UnityEngine.MeshRenderer", "path": "sharedMaterial", "value": {"name": "MonumentMat"}})
    u.call("set_property", {"target": "Orb", "component": "UnityEngine.MeshRenderer", "path": "sharedMaterial", "value": {"name": "OrbMat"}})

    step("写摄像机控制脚本并编译")
    u.call("write_script", {"path": "Assets/Scripts/CameraController.cs", "content": CAMERA_SCRIPT})
    u.call("compile")
    u.wait_compile_idle(timeout=300, verbose=False)
    st = u.call("compile_status")
    print("编译错误数:", len(st.get("errors", [])), flush=True)
    for e in st.get("errors", []):
        print("  error:", e.get("message"), flush=True)
    assert len(st.get("errors", [])) == 0

    step("挂到 Main Camera 并指向纪念碑")
    u.call("add_component", {"target": "Main Camera", "type": "CameraController"})
    u.call("set_property", {"target": "Main Camera", "component": "CameraController", "path": "target", "value": {"name": "Monument"}})
    u.call("set_property", {"target": "Main Camera", "component": "CameraController", "path": "distance", "value": 9})
    u.call("set_property", {"target": "Main Camera", "component": "CameraController", "path": "height", "value": 3.5})

    step("编辑模式截图")
    s = u.call("screenshot", {"width": 900, "height": 560})
    u.get_file(s["path"], os.path.join(os.path.dirname(os.path.abspath(__file__)), "cam_edit.png"))

    step("进 Play Mode,摄像机自动环绕")
    u.try_call("playmode", {"action": "enter"})
    u.ping_until(timeout=180, verbose=False)
    time.sleep(2.0)
    s1 = u.call("screenshot", {"width": 900, "height": 560})
    u.get_file(s1["path"], os.path.join(os.path.dirname(os.path.abspath(__file__)), "cam_play_1.png"))
    time.sleep(1.5)
    s2 = u.call("screenshot", {"width": 900, "height": 560})
    u.get_file(s2["path"], os.path.join(os.path.dirname(os.path.abspath(__file__)), "cam_play_2.png"))
    u.try_call("playmode", {"action": "exit"})
    u.ping_until(timeout=180, verbose=False)

    step("保存场景,完成")
    u.call("save_scene", {"path": "Assets/Scenes/CameraDemo.unity"})
    print("DONE: cam_edit.png / cam_play_1.png / cam_play_2.png", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FAILED:", e, file=sys.stderr)
        sys.exit(1)
