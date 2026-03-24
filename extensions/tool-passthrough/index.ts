import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

const plugin = {
  id: "tool-passthrough",
  name: "Tool Result Passthrough",
  description: "Appends URL reminder to search tool results.",

  register(api: OpenClawPluginApi) {
    (api as any).on("tool_result_persist", (event: any) => {
      const msg = event.message;
      if (!msg || msg.role !== "toolResult") return;
      if (event.toolName !== "web_fetch") return;

      const content = Array.isArray(msg.content) ? msg.content : [];
      const newContent = content.map((block: any) => {
        if (block.type !== "text") return block;
        const text: string = block.text ?? "";
        if (!text.includes("→")) return block;

        // Extract lines with URLs and build mandatory output
        const lines = text.split("\n").filter((l: string) => l.includes("→"));
        const urlList = lines.map((l: string) => {
          const parts = l.split("→");
          const url = parts[parts.length - 1].trim();
          const title = parts[0].replace(/^-\s*/, "").split(":")[0].trim();
          return title + ": " + url;
        }).join("\n");

        return {
          ...block,
          text: text + "\n\n=== MANDATORY OUTPUT - COPY EXACTLY ===\nAfter listing events, you MUST add this section:\n\nLinks:\n" + urlList + "\n=== END MANDATORY OUTPUT ==="
        };
      });

      return { message: { ...msg, content: newContent } };
    });
  }
};

export default plugin;
