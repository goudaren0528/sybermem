import { feedbackRpc, feedbackGate, sameLocation, type FeedbackNotice, type FeedbackStatus } from "./v2_feedback"

interface TuiContext {
  location?: { directory: string }
  data?: { listen(listener: (event: unknown) => void): () => void }
  ui: { router: { current(): { type: string; sessionID?: string } }; toast: { show(input: { title: string; message: string; variant: "info"; duration: number; sessionID: string }): void } }
  client: { rpc(definition: typeof feedbackRpc): {
    status(input: { sessionID: string }): Promise<FeedbackStatus>
    events: { on(name: "notice", listener: (event: { location?: { directory?: string }; data: FeedbackNotice }) => void): () => void }
  } }
}

export function setupSyberMemTui(ctx: TuiContext, refreshMs = 2000): () => void {
  const directory = ctx.location?.directory
  if (!directory) return () => {}
  const rpc = ctx.client.rpc(feedbackRpc)
  let stopped = false
  let selected: string | undefined
  let ticks = 0
  let generation = 0
  let pending: { sessionID: string; generation: number; queued: boolean } | undefined
  const active = (sessionID: string) => sameLocation(ctx.location?.directory, directory) && ctx.ui.router.current().type === "session" && ctx.ui.router.current().sessionID === sessionID
  const gate = feedbackGate(directory, () => ctx.ui.router.current(), (notice) => {
    if (!stopped && active(notice.sessionID)) ctx.ui.toast.show({ title: "SyberMem", message: notice.message, variant: "info", duration: notice.kind === "summary" ? 3500 : 5000, sessionID: notice.sessionID })
  })
  const refresh = (force = false) => {
    if (stopped) return
    const route = ctx.ui.router.current()
    const sessionID = sameLocation(ctx.location?.directory, directory) && route.type === "session" ? route.sessionID : undefined
    if (sessionID !== selected) { selected = sessionID; ++generation; pending = undefined; force = true }
    if (!force) return
    if (!sessionID) return
    if (pending) { pending.queued = true; return }
    const task = { sessionID, generation, queued: false }
    pending = task
    const revision = gate.revision(sessionID)
    const challenge = gate.challenge(sessionID)
    void Promise.resolve().then(() => rpc.status({ sessionID })).then((status) => {
      if (!stopped && task === pending && task.generation === generation && active(sessionID)) gate.restore(status, sessionID, revision, challenge)
    }).catch(() => { /* server may still be activating; next refresh retries */ }).finally(() => {
      if (task !== pending) return
      pending = undefined
      if (task.queued && !stopped) refresh(true)
    })
  }
  // RPC subscriptions are live-only. Subscribe before requesting the snapshot;
  // ordinary server activity wakes route checks, with a bounded quiet fallback.
  const off = rpc.events.on("notice", (event) => {
    refresh()
    if (!stopped && sameLocation(ctx.location?.directory, directory) && gate.accept(event)) refresh(true)
  })
  const offData = ctx.data?.listen(() => refresh(true))
  refresh()
  const timer = setInterval(() => { refresh(++ticks % 5 === 0) }, refreshMs)
  return () => {
    if (stopped) return
    stopped = true; ++generation; pending = undefined; clearInterval(timer)
    // A faulty disposer must not keep another listener or gate alive.
    try { offData?.() } catch { /* continue cleanup */ }
    try { off() } catch { /* continue cleanup */ }
    gate.clear()
  }
}

export default { id: "sybermem-tui", setup: setupSyberMemTui }
