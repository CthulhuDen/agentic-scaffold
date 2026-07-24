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

// EXIT_DRIFT in tools/sync-agents.py. The check's stderr is not surfaced here, so the status is
// the only thing that says which notice to show; every other status means regenerating won't help.
const EXIT_DRIFT = 3

type Notice = { title: string; message: string }

const DRIFT: Notice = {
  title: "agent files out of date",
  message: ".opencode/agents/ is stale relative to .claude/agents/. Run: tools/sync-agents.py",
}
const CHECK_FAILED: Notice = {
  title: "agent file check failed",
  message: "tools/sync-agents.py --check did not report drift. Run it to see why.",
}
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
  // Outside the try: a git failure here is not a verdict on the check, and classifying it as one
  // would blame a script that never ran. The caller logs the rejection instead.
  const cacheDir = await uvCacheDir(cwd)

  let notice: Notice
  try {
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
  } catch (err) {
    // Non-zero exit — treat as "needs the user's attention" and surface.
    const code = (err as { code?: unknown }).code
    // Spawn failure (uv absent, cwd gone): the check never ran, so there is no verdict to report
    // and no remedy a notice could name. Stay silent rather than nag on every prompt.
    if (code === "ENOENT") return
    notice = code === EXIT_DRIFT ? DRIFT : CHECK_FAILED
  }

  await showToast(client, cwd, notice)
  if (IS_DESKTOP_SIDECAR) await showMacNotification(notice)
  console.error(`[sync-agents-check] ${notice.title}: ${notice.message}`)
}

async function uvCacheDir(cwd: string): Promise<string> {
  const { stdout } = await exec("git", ["rev-parse", "--path-format=absolute", "--git-common-dir"], { cwd })
  return join(dirname(stdout.trim()), ".tmp", "uv-cache")
}

async function showToast(client: Client, directory: string, notice: Notice): Promise<void> {
  try {
    await client.tui.showToast({
      query: { directory },
      body: { ...notice, variant: "warning", duration: TOAST_DURATION_MS },
    })
  } catch (err) {
    console.error(`[sync-agents-check] tui.showToast failed:`, err)
  }
}

async function showMacNotification(notice: Notice): Promise<void> {
  if (platform() !== "darwin") return
  const script = `display notification "${escapeAppleScript(notice.message)}" with title "${escapeAppleScript(notice.title)}"`
  try {
    await exec("osascript", ["-e", script])
  } catch (err) {
    console.error(`[sync-agents-check] osascript failed:`, err)
  }
}

function escapeAppleScript(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/"/g, '\\"')
}
