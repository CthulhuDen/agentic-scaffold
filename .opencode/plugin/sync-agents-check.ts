// Warn when .opencode/agents/ is stale vs .claude/agents/. Fires on every user prompt:
// opencode has no `session.resume` event, so `chat.message` is the simplest substitute.
//
// Uses node:child_process rather than the SDK's `$` Bun shell helper because the desktop
// app's sidecar runs plugins under Node, where `$` is undefined despite being in the
// declared PluginInput type.

import { execFile } from "node:child_process"
import { platform } from "node:os"
import { dirname, join } from "node:path"
import { execPath } from "node:process"
import { promisify } from "node:util"

import type { Plugin } from "@opencode-ai/plugin"

type Client = Parameters<Plugin>[0]["client"]

const exec = promisify(execFile)

// The desktop sidecar runs from inside OpenCode.app. Today the desktop UI does not render
// `tui.toast.show` events, so we add a macOS notification there. The toast itself is
// always attempted — when the desktop starts rendering toasts, drop the notification.
const IS_DESKTOP_SIDECAR = execPath.includes("OpenCode.app/")

const TITLE = "agent files out of date"
const MESSAGE =
  ".opencode/agents/ is stale relative to .claude/agents/. Run: tools/sync-agents.py"
const TOAST_DURATION_MS = 10_000

export const SyncAgentsCheck: Plugin = async ({ client, directory }) => {
  return {
    "chat.message": async () => {
      // Fire-and-forget: never block the prompt on a subprocess, never propagate
      // hook errors into opencode's prompt pipeline.
      void runCheck(client, directory).catch((err) => {
        console.error(`[sync-agents-check] check failed:`, err)
      })
    },
  }
}

async function runCheck(client: Client, cwd: string): Promise<void> {
  try {
    const cacheDir = await uvCacheDir(cwd)
    await exec("uv", [
      "run",
      "--cache-dir",
      cacheDir,
      "--script",
      "tools/sync-agents.py",
      "--check",
      "--opencode",
    ], { cwd })
    return
  } catch {
    // Non-zero exit (or spawn failure) — treat as "needs the user's attention" and surface.
  }

  await showToast(client, cwd)
  if (IS_DESKTOP_SIDECAR) await showMacNotification()
  console.error(`[sync-agents-check] ${TITLE}: ${MESSAGE}`)
}

async function uvCacheDir(cwd: string): Promise<string> {
  const { stdout } = await exec("git", ["rev-parse", "--path-format=absolute", "--git-common-dir"], { cwd })
  return join(dirname(stdout.trim()), ".tmp", "uv-cache")
}

async function showToast(client: Client, directory: string): Promise<void> {
  try {
    await client.tui.showToast({
      query: { directory },
      body: { title: TITLE, message: MESSAGE, variant: "warning", duration: TOAST_DURATION_MS },
    })
  } catch (err) {
    console.error(`[sync-agents-check] tui.showToast failed:`, err)
  }
}

async function showMacNotification(): Promise<void> {
  if (platform() !== "darwin") return
  const script = `display notification "${escapeAppleScript(MESSAGE)}" with title "${escapeAppleScript(TITLE)}"`
  try {
    await exec("osascript", ["-e", script])
  } catch (err) {
    console.error(`[sync-agents-check] osascript failed:`, err)
  }
}

function escapeAppleScript(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/"/g, '\\"')
}
