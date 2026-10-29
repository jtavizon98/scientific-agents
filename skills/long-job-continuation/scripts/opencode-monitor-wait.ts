// OpenCode V2 plugin that provides the `monitor_wait` tool for the
// long-job-continuation skill. Place it (or a symlink to it) in
// .opencode/plugins/ of the project. It runs monitor_wait.py from the skill's
// scripts directory; set MONITOR_WAIT_SCRIPT to use another copy. The plugin
// API usage was extracted from a working setup but is not exercised by the
// repository tests; check it against your OpenCode version.
import { createHash } from "node:crypto"
import { spawn } from "node:child_process"
import { fileURLToPath } from "node:url"
import { Plugin } from "@opencode/plugin"

type CommandResult = {
  code: number
  stdout: string
  stderr: string
}

type MonitorWaitInput = {
  contract: string
  timeout_seconds?: number
}

function runWait(
  script: string,
  args: string[],
  cwd: string,
  signal: AbortSignal,
): Promise<CommandResult> {
  return new Promise((resolve, reject) => {
    const child = spawn("python3", [script, ...args], {
      cwd,
      stdio: ["ignore", "pipe", "pipe"],
    })
    let stdout = ""
    let stderr = ""
    let killTimer: ReturnType<typeof setTimeout> | undefined

    child.stdout.setEncoding("utf8")
    child.stderr.setEncoding("utf8")
    child.stdout.on("data", (chunk) => (stdout += chunk))
    child.stderr.on("data", (chunk) => (stderr += chunk))

    const abort = () => {
      child.kill("SIGTERM")
      killTimer = setTimeout(() => child.kill("SIGKILL"), 5000)
    }
    if (signal.aborted) abort()
    else signal.addEventListener("abort", abort, { once: true })

    child.on("error", reject)
    child.on("close", (code) => {
      signal.removeEventListener("abort", abort)
      if (killTimer) clearTimeout(killTimer)
      resolve({ code: code ?? 1, stdout: stdout.trim(), stderr: stderr.trim() })
    })
  })
}

export default Plugin.define({
  id: "agent.long-job-continuation",
  async setup(ctx) {
    const worktree = ctx.location.project.directory
    // The wait script resolves the project root and the sessions directory itself.

    await ctx.tool.transform((editor) => {
      editor.add({
        name: "monitor_wait",
        description:
          "Wait for a reviewed PanDA, Slurm, or dependency monitor contract. " +
          "Use this instead of polling or delegating a polling subagent. The tool " +
          "blocks without model calls, fails fast on attention states, and returns " +
          "durable evidence to this same parent turn.",
        input: {
          type: "object",
          properties: {
            contract: {
              type: "string",
              description: "Project-relative path to a reviewed wait-contract JSON file",
            },
            timeout_seconds: {
              type: "number",
              exclusiveMinimum: 0,
              description: "Optional bound no longer than the contract timeout",
            },
          },
          required: ["contract"],
          additionalProperties: false,
        },
        async execute(input, context) {
          const args = input as MonitorWaitInput
          const script = process.env.MONITOR_WAIT_SCRIPT ??
            fileURLToPath(new URL("./monitor_wait.py", import.meta.url))
          const eventID = createHash("sha256")
            .update(`${context.sessionID}\0${context.messageID}\0${args.contract}`)
            .digest("hex")
            .slice(0, 32)
          const command = [
            "wait",
            "--contract",
            args.contract,
            "--session-id",
            context.sessionID,
            "--message-id",
            context.messageID,
            "--owner-pid",
            String(process.pid),
            "--event-id",
            eventID,
          ]
          if (args.timeout_seconds !== undefined) {
            command.push("--timeout-seconds", String(args.timeout_seconds))
          }

          await context.progress({
            title: `Waiting on monitor contract ${args.contract}`,
            eventID,
            contract: args.contract,
          })
          const result = await runWait(script, command, worktree, context.signal)
          if (!result.stdout) {
            throw new Error(result.stderr || `monitor wait exited with ${result.code}`)
          }
          let payload: unknown
          try {
            payload = JSON.parse(result.stdout)
          } catch {
            throw new Error(`monitor wait returned invalid JSON: ${result.stdout}`)
          }
          return {
            content:
              JSON.stringify(payload, null, 2) +
              "\n\nContinue only within the recorded post-handback authorization. " +
              "Scheduler completion is not output validation.",
            metadata: { eventID, contract: args.contract, exitCode: result.code },
          }
        },
      })
    })
  },
})
