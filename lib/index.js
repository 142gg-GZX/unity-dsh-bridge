import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const PROVIDER_NAME = "unity-dsh-bridge";
const SKILL_BODY_URL = new URL("../assets/skill.md", import.meta.url);
const RESOURCE_BASE = {
  kind: "directory",
  path: fileURLToPath(new URL("../assets/", import.meta.url))
};
const CANDIDATE = {
  name: "unity-dsh-bridge",
  description: "通过本机 HTTP 桥接直接控制 Unity/团结引擎编辑器——搭场景、写 C# 脚本、编译排错、进 Play Mode、截图、模拟输入,实现边看边调的闭环。当用户要求在 Unity 里做/改/调试游戏内容时使用。",
  invocation: { modelInvocable: true, userInvocable: true },
  provider: PROVIDER_NAME,
  source: "bundled",
  resourceBase: RESOURCE_BASE,
  rank: 600,
  locator: SKILL_BODY_URL
};
const provider = {
  name: PROVIDER_NAME,
  list: () => Promise.resolve([CANDIDATE]),
  async get(_candidate) {
    return {
      name: CANDIDATE.name,
      description: CANDIDATE.description,
      invocation: CANDIDATE.invocation,
      provider: CANDIDATE.provider,
      source: CANDIDATE.source,
      resourceBase: RESOURCE_BASE,
      content: await readFile(SKILL_BODY_URL, "utf8")
    };
  }
};
const name = "skill-unity-dsh-bridge";
const inject = ["skills"];
function apply(ctx) {
  ctx.skills.registerProvider(() => provider);
}
export { apply, inject, name };
