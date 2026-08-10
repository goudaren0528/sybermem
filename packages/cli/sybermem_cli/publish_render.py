from __future__ import annotations


def render_publish_status_text(payload: dict) -> int:
    if payload.get("status") == "blocked":
        print("Publish preview blocked:")
        print(f"- reason: {payload['reason']}")
        if payload.get("project"):
            print(f"- project path: {payload['project']['path']}")
        return 1
    if payload.get("status") == "preview":
        print("Publish preview for Team repo:")
        print(f"- team: {payload['team_id']}")
        print(f"- project: {payload['slug']}")
        print(f"- source revision: {payload['source_revision']}")
        print(f"- memory source hash: {payload['source_hash']}")
        if payload.get("source_scope"):
            print(f"  (scope: {payload['source_scope']} — a stale-preview guard over project memory, not a full publish-safety proof)")
        print(f"- freshness: {payload['freshness']}")
        print(f"- review required: {'yes' if payload.get('review_required') else 'no'}")
        return 0
    if payload.get("status") == "stale_preview":
        print("Publish rejected: stale preview (project memory changed since the reviewed preview)")
        print(f"- expected memory source hash: {payload['expected_source_hash']}")
        print(f"- current memory source hash: {payload['preview']['source_hash']}")
        return 1

    print("Published project summary to Team repo:")
    print(f"- team: {payload['team_id']}")
    print(f"- project: {payload['slug']}")
    if payload.get('source_phase_digest'):
        print(f"- latest phase digest: {payload['source_phase_digest']}")
    if payload.get('source_theme_digest'):
        print(f"- latest theme digest: {payload['source_theme_digest']}")
    print("- files:")
    for file_path in payload["files"]:
        print(f"  - {file_path}")
    if payload.get("pushed"):
        print("- pushed to remote: yes")
    else:
        print("- pushed to remote: no (push manually or check remote config)")
    print("- suggested follow-up: /sybermem-team-summary")
    return 0
