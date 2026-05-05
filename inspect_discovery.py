"""One-off discovery inspector. Surfaces the raw data and decisions
behind a Red Queen run so you can see what's matched, clustered,
scored, and rejected — not just the final counts.
"""
import asyncio
import re
from datetime import datetime
from collections import defaultdict

from agents.red_queen import RedQueen, RedditMonitor, DataGovMonitor
from config.settings import config


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def truncate(s: str, n: int = 90) -> str:
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


async def main() -> None:
    monitor = RedditMonitor()
    session = await monitor._get_session()

    section("CONFIG")
    print(f"  subreddits: {config.discovery.reddit_subreddits}")
    print(f"  pain patterns: {len(monitor.PAIN_PATTERNS)}")
    print(f"  ev patterns:   {len(monitor.EV_SEARCH_PATTERNS)}")
    print(f"  mirrors (priority): {monitor.PUSHSHIFT_MIRRORS}")

    section("PER-SUBREDDIT FETCH + PAIN MATCHES")
    raw_by_sub: dict = {}
    matches_by_sub: dict = defaultdict(list)
    pattern_hits: dict = defaultdict(int)

    for sub in config.discovery.reddit_subreddits:
        posts = await monitor._fetch_subreddit_posts(session, sub)
        raw_by_sub[sub] = posts
        if not posts:
            print(f"\n  r/{sub}: 0 posts")
            continue

        newest = datetime.fromtimestamp(max(p.get("created_utc", 0) for p in posts))
        oldest = datetime.fromtimestamp(min(p.get("created_utc", 0) for p in posts))
        print(f"\n  r/{sub}: {len(posts)} posts | range {oldest.date()} → {newest.date()}")

        for post in posts:
            text = f"{post.get('title','')} {post.get('selftext','')}".lower()
            hit = None
            for pat in monitor.PAIN_PATTERNS:
                if re.search(pat, text):
                    hit = ("pain", pat)
                    break
            if not hit:
                for pat in monitor.EV_SEARCH_PATTERNS:
                    if re.search(pat, text):
                        hit = ("ev", pat)
                        break
            if hit:
                kind, pat = hit
                pattern_hits[f"{kind}:{pat}"] += 1
                matches_by_sub[sub].append((pat, post))

        if matches_by_sub[sub]:
            print(f"    matched {len(matches_by_sub[sub])} pain post(s):")
            for pat, post in matches_by_sub[sub][:5]:
                ts = datetime.fromtimestamp(post.get("created_utc", 0))
                eng = post.get("score", 0) + post.get("num_comments", 0)
                print(f"      • [{ts.date()}] eng={eng:>4} pattern='{pat}'")
                print(f"        {truncate(post.get('title',''), 100)}")

    section("PATTERN HIT FREQUENCY")
    if not pattern_hits:
        print("  (none)")
    else:
        for key, n in sorted(pattern_hits.items(), key=lambda x: -x[1]):
            print(f"  {n:>3}  {key}")

    section("PAIN POINTS → THEMES → PIVOTS")
    # Build pain points from the already-fetched posts so this section is
    # consistent with the per-subreddit match report above. Calling
    # monitor.scan_subreddits() here would trigger a second network fetch
    # whose snapshot may differ from the first.
    pain_points = []
    for sub, posts in raw_by_sub.items():
        for post in posts:
            pain = monitor._analyze_post(sub, post)
            if pain and monitor._dedupe(pain):
                pain_points.append(pain)
    if not pain_points and not config.is_production:
        for p in monitor._get_mock_pain_points():
            if monitor._dedupe(p):
                pain_points.append(p)

    print(f"\n  total pain points (from cached fetch): {len(pain_points)}")
    for p in pain_points:
        print(f"    • src={p.source} eng={p.engagement} sentiment={p.sentiment_score:+.2f}")
        print(f"      keywords={p.keywords}")
        print(f"      text={truncate(p.text, 100)}")

    rq = RedQueen()
    themes = rq._cluster_pain_points(pain_points)
    print(f"\n  themes clustered: {len(themes)}")
    for theme, pts in themes.items():
        print(f"    {theme}: {len(pts)} point(s)")

    datasets = await DataGovMonitor().get_recent_datasets()
    print(f"\n  datasets available: {len(datasets)}")

    section("PIVOT GATE EVALUATION")
    print("  Gate: pain_velocity >= 2.0  AND  competition_gap <= 0.8")
    accepted, rejected = [], []
    for theme, pts in themes.items():
        ds = rq._find_matching_datasets(theme, datasets)
        if not ds:
            rejected.append((theme, "no matching dataset", None, None))
            continue
        vel = rq._calculate_pain_velocity(pts)
        gap = rq._estimate_competition_gap(theme, pts)
        if vel < 2.0:
            rejected.append((theme, f"pain_velocity {vel:.2f} < 2.0", vel, gap))
        elif gap > 0.8:
            rejected.append((theme, f"competition_gap {gap:.2f} > 0.8", vel, gap))
        else:
            accepted.append((theme, vel, gap, ds))

    print(f"\n  accepted: {len(accepted)}")
    for theme, vel, gap, ds in accepted:
        print(f"    ✅ {theme}  velocity={vel:.2f} gap={gap:.2f} datasets={[d.name for d in ds]}")

    print(f"\n  rejected: {len(rejected)}")
    for theme, reason, vel, gap in rejected:
        v = f"{vel:.2f}" if vel is not None else "—"
        g = f"{gap:.2f}" if gap is not None else "—"
        print(f"    ❌ {theme}  velocity={v} gap={g}  reason: {reason}")

    await session.close()


if __name__ == "__main__":
    asyncio.run(main())
