import { expect, test } from "bun:test";
import { readFile } from "node:fs/promises";
import plugin from "../index.js";

test("registers bundled skills and commands while preserving prompt attachments and delivery", async () => {
  const skills = [];
  const commands = [];
  const prompts = [];
  await plugin.setup({
    skill: { transform: async (transform) => transform({ add: (skill) => skills.push(skill) }) },
    command: { transform: async (transform) => transform({ add: (command) => commands.push(command) }) },
    session: { prompt: async (prompt) => prompts.push(prompt) },
  });
  expect(new Set(skills.map((skill) => skill.id)).size).toBe(skills.length);
  expect(commands.map((command) => command.name)).toContain("pstack:poteto-help");
  expect(commands.some((command) => command.name.startsWith("pstack:principle-"))).toBe(false);
  expect(skills.filter((skill) => skill.autoinvoke !== false).map((skill) => skill.id)).toEqual([]);
  const poteto = skills.find((skill) => skill.id === "pstack-poteto-mode");
  expect(poteto.autoinvoke).toBe(false);
  expect(await readFile(poteto.path, "utf8")).toContain(poteto.content);
  expect(poteto.content).toContain("../opencode-runtime.md");
  const prompt = { text: "Review @app.ts", files: [{ path: "app.ts", mention: { start: 7, end: 14 } }] };
  await commands.find((command) => command.name === "pstack:poteto-mode").execute({ sessionID: "test-session", prompt, delivery: "queue" });
  expect(prompts).toHaveLength(1);
  expect(prompts[0]).toEqual({ ...prompt, sessionID: "test-session", delivery: "queue", text: expect.stringContaining("Review @app.ts\n\nLoad the `pstack-poteto-mode` skill") });
  expect(prompts[0].files).toBe(prompt.files);
});
