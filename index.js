import { readFile, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

export default {
  id: "pstack",
  async setup(ctx) {
    const skills = [];
    for (const entry of await readdir(new URL("./skills/", import.meta.url), { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const path = fileURLToPath(new URL(`./skills/${entry.name}/SKILL.md`, import.meta.url));
      const text = await readFile(path, "utf8");
      const header = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(text);
      if (!header) throw new Error(`Missing skill frontmatter: ${path}`);
      const metadata = Bun.YAML.parse(header[1]);
      if (metadata.name !== entry.name || typeof metadata.description !== "string") {
        throw new Error(`Invalid skill name or description: ${path}`);
      }
      skills.push({
        id: `pstack-${entry.name}`,
        name: metadata.name,
        description: metadata.description,
        path,
        content: text.slice(header[0].length).trim(),
        autoinvoke: metadata.metadata?.["opencode/autoinvoke"] !== false,
      });
    }
    await ctx.skill.transform((editor) => {
      for (const skill of skills) editor.add(skill);
    });
    await ctx.command.transform((editor) => {
      for (const skill of skills) {
        if (skill.id.startsWith("pstack-principle-")) continue;
        editor.add({
          name: `pstack:${skill.id.slice("pstack-".length)}`,
          description: skill.description,
          execute: ({ sessionID, prompt, delivery }) => ctx.session.prompt({
            ...prompt,
            sessionID,
            delivery,
            text: `${prompt.text ?? ""}\n\nLoad the \`${skill.id}\` skill with the skill tool and follow it for this request. Read its linked OpenCode runtime contract first.`,
          }),
        });
      }
    });
  },
};
