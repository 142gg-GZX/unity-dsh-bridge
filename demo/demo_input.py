#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按键控制相机 + AI 模拟输入验证"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "client"))
import unity_client as u

def step(msg):
    u.try_call("set_status", {"text": msg}, timeout=5)
    print(msg, flush=True)

CAM = r'''using UnityEngine;
using System.Collections;

public class CameraController : MonoBehaviour
{
    public float moveSpeed = 6f;

    void Update()
    {
        float h = Input.GetAxisRaw("Horizontal");
        float v = Input.GetAxisRaw("Vertical");
        float up = 0f;
        if (Input.GetKey(KeyCode.Q)) up -= 1f;
        if (Input.GetKey(KeyCode.E)) up += 1f;

        Vector3 dir = (transform.right * h + transform.forward * v + transform.up * up);
        if (dir.sqrMagnitude > 1f) dir.Normalize();
        transform.position += dir * moveSpeed * Time.deltaTime;
    }

    Vector3 DirFor(string key)
    {
        switch (key.ToUpper())
        {
            case "W": return transform.forward;
            case "S": return -transform.forward;
            case "D": return transform.right;
            case "A": return -transform.right;
            case "E": return transform.up;
            case "Q": return -transform.up;
            default: return Vector3.zero;
        }
    }

    public void SimulateKey(string key, float duration)
    {
        StartCoroutine(SimulateRoutine(key, Mathf.Max(0.01f, duration)));
    }

    IEnumerator SimulateRoutine(string key, float duration)
    {
        Vector3 dir = DirFor(key);
        float t = 0f;
        while (t < duration)
        {
            transform.position += dir * moveSpeed * Time.deltaTime;
            t += Time.deltaTime;
            yield return null;
        }
    }

    public static void Simulate(string key, float duration)
    {
        GameObject go = GameObject.Find("Main Camera");
        if (go == null) return;
        CameraController cam = go.GetComponent<CameraController>();
        if (cam != null) cam.SimulateKey(key, duration);
    }
}
'''

def shot(name):
    s = u.call("screenshot", {"width": 900, "height": 560})
    u.get_file(s["path"], os.path.join(os.path.dirname(os.path.abspath(__file__)), name))
    return s

def cam_pos():
    return u.call("get_property", {"target": "Main Camera", "component": "UnityEngine.Transform", "path": "position"})

def main():
    step("等待桥接就绪")
    u.ping_until(timeout=300, verbose=False)

    step("确保在编辑模式")
    st = u.try_call("playmode_state")
    if st.get("playing") or st.get("changing"):
        u.try_call("playmode", {"action": "exit"})
        u.ping_until(timeout=120, verbose=False)
    u.wait_compile_idle(timeout=300, verbose=False)

    step("重写相机脚本:WASD/QE 飞行 + AI 模拟入口")
    u.call("write_script", {"path": "Assets/Scripts/CameraController.cs", "content": CAM})
    u.call("compile")
    u.wait_compile_idle(timeout=300, verbose=False)
    st = u.call("compile_status")
    print("编译错误数:", len(st.get("errors", [])), flush=True)
    for e in st.get("errors", []):
        print("  error:", e.get("message"), flush=True)
    assert len(st.get("errors", [])) == 0

    step("挂组件 + 摆好相机")
    u.call("add_component", {"target": "Main Camera", "type": "CameraController"})
    u.call("set_transform", {"target": "Main Camera", "position": [0, 3, -9], "rotation": [0, 0, 0]})

    step("进 Play Mode")
    u.try_call("playmode", {"action": "enter"})
    u.ping_until(timeout=180, verbose=False)
    time.sleep(1.0)

    step("模拟输入前:记录相机位置并截图")
    p0 = cam_pos()
    shot("input_0_before.png")
    print("before pos:", json.dumps(p0), flush=True)

    step("模拟按住 D 键 2 秒(向右移动)")
    u.call("invoke_static", {"type": "CameraController", "method": "Simulate", "args": ["D", 2.0]})
    time.sleep(1.0)
    p1 = cam_pos()
    shot("input_1_during.png")
    print("during pos:", json.dumps(p1), flush=True)
    time.sleep(1.6)
    p2 = cam_pos()
    shot("input_2_after.png")
    print("after pos:", json.dumps(p2), flush=True)

    step("退出 Play Mode 并保存")
    u.try_call("playmode", {"action": "exit"})
    u.ping_until(timeout=180, verbose=False)
    u.call("save_scene", {"path": "Assets/Scenes/CameraDemo.unity"})
    print("DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FAILED:", e, file=sys.stderr)
        sys.exit(1)
