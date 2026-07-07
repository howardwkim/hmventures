# /social-package

## BRAND RULE — READ THIS FIRST, NO EXCEPTIONS

Before generating any content, read every file in the brand folder:

```
C:\Users\mike\viral-topics\brands\miho\
```

Read all files present:
- `brand-dna.md` — positioning, competitors, core mechanism, offer, hard rules
- `brand-voice.md` — voice rules, do/don't word list, tone by context
- `icp.md` — the 3 personas, pain points, objections, transformation they're buying
- `proven-angles.md` — confirmed angles that have won. These override assumptions.

Also read:
```
C:\Users\mike\viral-topics\config\voice_profile.json
```

**Brand files are ground truth. Never write a word without loading them first.**

---

You are the distribution engine for MiHO Partners content. The article has already been written, approved by Mike, and saved. Your job is to take that article and produce a full week of platform-optimized content — one topic, every platform, everything scheduled or ready to go.

---

## PHASE 1 — LOAD THE APPROVED ARTICLE

Find the most recently approved article:

```python
import glob, os
files = glob.glob(r'C:\Users\mike\viral-topics\approved_articles\miho\*.md')
latest = max(files, key=os.path.getmtime)
print(latest)
```

Read that file. Extract:
- **Title**
- **Core topic / theme**
- **Mike's main stance or POV**
- **The key story or client example**
- **The fix or takeaway**
- **The CTA question** (if present)

Then say exactly this to Mike:

> "Working from: **[TITLE]** ([DATE])
> Topic: [ONE SENTENCE SUMMARY OF THE CORE IDEA]
>
> That the right one? Or paste a different article."

Wait for Mike's confirmation before proceeding.

---

## PHASE 2 — PLATFORM SELECTION

Once Mike confirms the article, ask:

> "Which platforms are we creating for this week?"

List the available options:
- LinkedIn (carousel by default — no avatar, text/image format; occasionally a talking-head video instead, see note below)
- X (thread or hot take by default — no avatar; occasionally video too)
- YouTube (Shorts — avatar video by default)
- TikTok (avatar video by default)
- Instagram (Reel — avatar video by default, or Carousel for checklist/step-by-step topics)
- Newsletter (Beehive copy)

**Current default: LinkedIn only.** If Mike doesn't specify, proceed with LinkedIn.

**Format routing (decided 2026-07-06, refined 2026-07-06):** TikTok, Instagram, and YouTube are talking-head platforms — avatar video is the right format and the default execution path (Phase 7B produces the actual video and posts it via WoopSocial). LinkedIn and X **default** to text/image/carousel since that already gets good engagement without a talking head — but **from time to time Mike wants an actual talking-head video on LinkedIn (and possibly X)**, not as the norm, as an occasional format. This routing may get more nuanced once real performance data comes in.

**If Mike asks for a LinkedIn or X video specifically:** ask which execution he wants — a dedicated avatar for LinkedIn/X content (may differ from the TikTok/IG/YouTube avatar — more formal/professional look could fit LinkedIn's tone better) or Mike filming it live himself. Not decided yet which is the standing choice; ask each time until Mike settles on one. If avatar, it still routes through Phase 7B same as the other platforms — just confirm which avatar identity to use since it may not be the default `AVATAR-MIKE.md` look.

**If TikTok, Instagram, or YouTube is selected**, ask once (not per-platform): *"Avatar video (I generate and post it automatically) or script only (you film it yourself)?"* Default to avatar video if Mike doesn't specify — that's the whole point of the automation. A platform can still be script-only if Mike says so for that one.

Run each selected platform's phase below. Run them in parallel when more than one is selected. Video platforms in avatar mode all funnel into **Phase 7B** after their script is written — that's the shared HeyGen production step, not repeated per platform.

---

## PHASE 3 — LINKEDIN CAROUSEL

LinkedIn document carousels outperform every other format (7% engagement vs 4.3% for text). This is the core LinkedIn output.

### What you produce:
1. **8-slide carousel script** — Mike takes this to Canva, builds the PDF, uploads to LinkedIn
2. **Caption** — the text that appears above the carousel on LinkedIn (the scroll-stopper)
3. **First comment** — the follow-up comment Mike posts immediately after (boosts reach in first 60 minutes)

### Carousel structure:

**Slide 1 — Hook**
Pull the strongest line from the article's opening. Must work as a standalone statement that stops a scroll. 2-4 lines max. No setup, no context — just the hook.

**Slides 2-6 — Content (one idea per slide)**
Each slide carries one point from the article. Keep each slide to 4-8 lines. Short sentences. Each slide must be able to stand alone — someone dropping in mid-carousel should still follow it. Use the article's structure: problem → diagnosis → fix → pattern → implication. Don't cram every nuance in — pick the sharpest version of each point.

**Slide 7 — The Insight**
The one thing you want them to remember. The line from the article that earns the most "that's exactly it" reactions. Often the diagnosis line or the pattern Mike's seen for years. This is the slide people screenshot.

**Slide 8 — CTA**
The question. Pulled from or inspired by the article's CTA. Short. Genuine. Not "follow me for more" — a real question that invites a real reply. End with Mike's name.

### Voice rules for carousel (non-negotiable):
- Short lines — 6 words or fewer where possible on each line break
- No em dashes. Period.
- No hedging ("might", "could", "it's worth noting")
- No AI tells ("game-changer", "crucial", "elevate", "in today's landscape")
- Same dry humor as the article — if a Brad reference or equivalent fits, use it
- Each slide is a beat in a story, not a bullet list of facts

### Caption (appears above the carousel):
- 2-3 lines max
- Opens with a hook line that teases the carousel without giving it away
- Does NOT summarize the article — makes them want to swipe
- No hashtags in the caption body
- 2-3 hashtags at the very end on their own line

**Caption format:**
```
[Hook line — the tension or the surprising fact]
[1 line of context or stakes]
[Swipe prompt — e.g. "Swipe to see what we found." or "Here's what changed."]

#SmallBusiness #BusinessSystems #MiHO
```

### First comment (Mike posts immediately after):
```
Full article: [WordPress URL from the approved article frontmatter]
[One sentence teaser — what they'll get by clicking]
```

### Presentation format:

Show the output in this order:

---
**LINKEDIN CAROUSEL — [TITLE]**

**Caption (paste above the carousel when uploading):**
[caption]

**First Comment (post immediately after):**
[first comment]

---
**SLIDE 1**
[text]

**SLIDE 2**
[text]

...and so on through SLIDE 8.

---

After presenting, say:
> "Take the slide script to Canva, build the PDF (1080x1080 or 1920x1080 per slide), and upload to LinkedIn with that caption. Post on Tuesday or Thursday morning — those are your strongest LinkedIn windows. Drop the first comment within 5 minutes of posting."

---

## PHASE 4 — X THREAD *(add when ready)*

Placeholder. Will produce a 4-6 tweet thread using the article's sharpest contrarian angle or a single hot-take tweet if the topic is punchy enough.

---

## PHASE 5 — YOUTUBE SHORTS SCRIPT

YouTube Shorts gets 200B daily views and a 5.9% engagement rate — higher than TikTok. One tight idea per Short. No padding.

### What you produce:
1. **Hook line** — the first 3 seconds. Must stop the scroll on its own.
2. **Full spoken script** — ~150 words, 60 seconds. Word for word.
3. **On-screen text overlays** — 3-4 key phrases to flash on screen while talking
4. **YouTube description** — first 2 lines visible before "more" (the hook), then 3-4 lines of context, then 5 tags

### Script structure:

**0:00–0:03 — Hook**
A surprising stat, a bold claim, or a direct question. Must work with no setup. Examples: "83% of growing small businesses use AI tools. 55% of declining ones don't." or "Your solopreneur competitor isn't smarter than you."

**0:03–0:10 — Stakes**
Why should they keep watching. One or two sentences connecting the hook to their specific situation.

**0:10–0:50 — The one idea**
Problem → what most business owners get wrong → the actual fix. One point only. If there's more to say, that's a different Short.

**0:50–1:00 — CTA**
Ask a genuine question (same as the article CTA works well here). "Comment below: what task are you still doing manually that software could just handle?" End with name: "I'm Mike Grabham. Follow for more of this."

### Voice rules:
- Short sentences. Pause after each one. This is spoken word, not written.
- No corporate tone. Talk like you're explaining it to a client over coffee.
- Numbers anchor everything: "$500/month", "83%", "twice as many"
- Same dry humor as the article. If a Brad reference fits, use it.
- No em dashes. No hedging. No AI tells.

### Execution: avatar video (default) or script only

**If avatar mode** (default): this script feeds Phase 7B, which generates the HeyGen video and posts it to YouTube via WoopSocial automatically. Nothing further needed here — just write the script above.

**If script-only mode** (Mike said he wants to film this one himself): output the script only. Mike records and uploads directly to YouTube.

### Presentation format:

---
**YOUTUBE SHORTS — [TITLE]**

**Hook (first 3 seconds):**
[hook line]

**Script:**
[full word-for-word script]

**On-Screen Text Overlays:**
- [overlay 1]
- [overlay 2]
- [overlay 3]

**YouTube Description:**
[2-line hook]
[3-4 lines context]
Tags: [tag1] [tag2] [tag3] [tag4] [tag5]

---

---

## PHASE 6 — TIKTOK SCRIPT

TikTok's 3.70% engagement rate is driven almost entirely by UGC-style creator content — 4.2x more than polished brand content. This is the most casual, human output in the package.

### What you produce:
1. **Hook** — first 1-2 seconds, spoken AND suggested on-screen text
2. **Full script** — ~120 words, 30-45 seconds
3. **On-screen text suggestions** — what to overlay at each beat
4. **Caption** — short, punchy, first line is the hook
5. **Hashtags** — 5-7, mix of niche (#SmallBusiness, #SMBOwner) and broad (#BusinessTips, #Entrepreneur)

### Script structure:

**0:00–0:02 — Hook (everything rides on this)**
Spoken out loud AND shown as text overlay. Provocative statement or relatable frustration. "Your biggest competitor has zero employees." or "The reason you're losing quotes isn't your price."

**0:02–0:10 — The relatable setup**
The situation most small business owners recognize. Short. "Most small business owners are still doing [X] manually. They've been doing it for years. It feels normal."

**0:10–0:35 — The flip**
What they're missing. What the lean competitor is actually doing differently. Keep it concrete — one specific tool category or one specific task.

**0:35–0:45 — Payoff + follow ask**
The simple takeaway. Then: "Follow for more of this." or "If this hit different, follow — I post this every week."

### Voice rules:
- This is the most casual output. "Hey, real talk." energy.
- Shorter sentences than LinkedIn. Even choppier.
- Can lean into humor more than other platforms.
- Still no AI tells. No hedging. No em dashes.
- First person, direct. Like texting a friend who owns a business.

### Execution: avatar video (default) or script only

**If avatar mode** (default): this script feeds Phase 7B, which generates the HeyGen video and posts it to TikTok via WoopSocial (`postType: VIDEO`, `postMode: DIRECT_POST`, `isAiGeneratedContent: true`) automatically. Nothing further needed here — just write the script above.

**If script-only mode** (Mike said he wants to film this one himself): output script for Mike to record, then post via WoopSocial or directly in the TikTok app.

### Presentation format:

---
**TIKTOK — [TITLE]**

**Hook (0:00–0:02):**
Spoken: [hook line]
On-screen text: [text overlay]

**Script:**
[full word-for-word script with beat markers]

**On-Screen Overlays:**
- [beat + overlay suggestion]
- [beat + overlay suggestion]

**Caption:**
[caption — first line is hook]

**Hashtags:**
#SmallBusiness #[niche] #[niche] #BusinessTips #Entrepreneur

---

---

## PHASE 7 — INSTAGRAM

Instagram strategy for MiHO: **60% Reels (reach/discovery), 40% Carousels (depth/saves)**. Default to Reel unless the topic is checklist/step-by-step, in which case carousel wins.

### What you produce:

**Option A — Reel Script (default)**
Same structure as TikTok but slightly more polished delivery. 30-60 seconds. Hook in first 3 seconds is critical (Instagram algorithm weights early watch time heavily).

Produce:
1. **Hook** (first 3 sec)
2. **Full script** (~120-150 words)
3. **Caption** — Instagram cuts off at 125 characters before "more." First line must be the hook. Keep body 3-5 lines.
4. **Hashtags** — post in FIRST COMMENT, not caption body. 10-15 hashtags: mix of niche (#SmallBusinessOwner, #BusinessSystems, #MiHO) and broad (#Entrepreneur, #SmallBiz, #BusinessGrowth)
5. **Cover frame suggestion** — what should be on screen at frame 1 (Instagram shows this as the static preview)

**Option B — Carousel (use when topic = checklist, step-by-step, or comparison)**
5-7 slides. Same brand format as LinkedIn carousel but IG-native sizing (1080x1080). Slide 1 is the scroll-stopper hook image/headline. Last slide is always the CTA + follow ask.

Produce:
1. **Slide-by-slide copy** (shorter than LinkedIn — 2-4 lines per slide max for mobile)
2. **Caption** (hook line + 3-4 lines + CTA)
3. **Hashtags** (in first comment)

### Voice rules (both formats):
- Same MiHO voice as other platforms — no hedging, no AI tells, no em dashes
- Instagram audience skews slightly younger than LinkedIn — can be slightly more casual
- Visuals matter more here: always suggest what should be on screen
- Caption hook must work without seeing the video/image (shown in feed before autoplay starts)

### Execution: avatar video (default, Reel only) or script only

**If avatar mode** (default, Reel format only — Carousel is always script/manual): this script feeds Phase 7B, which generates the HeyGen video and posts it to Instagram via WoopSocial (`platform: INSTAGRAM`, `postType: REEL`) automatically. Nothing further needed here — just write the script above.

**If script-only mode, or Carousel format**: output script + caption — Mike records (or builds the carousel), then posts via WoopSocial with caption and image/video.

### Presentation format:

---
**INSTAGRAM REEL — [TITLE]**

**Hook (first 3 seconds):**
[hook]

**Cover frame:** [what to show on screen at frame 1]

**Script:**
[full script]

**Caption:**
[hook line]
[3-5 lines body]
[CTA line]

**First Comment (hashtags):**
#SmallBusiness #SmallBusinessOwner #BusinessSystems #MiHO #Entrepreneur #BusinessGrowth #[niche tag] #[niche tag] #[niche tag] #[niche tag]

---

---

## PHASE 7B — AVATAR VIDEO PRODUCTION (runs once, for any of TikTok/YouTube/Instagram-Reel set to avatar mode in Phase 2)

This is the shared HeyGen production step. It does not repeat per platform — it takes whichever scripts from Phases 5-7 were marked avatar mode and turns each into a real, posted video. Validated end-to-end 2026-07-06 (TikTok, Instagram Reel, YouTube Shorts all confirmed working with this exact flow).

**Before writing any avatar prompt: this content came from an approved article, so it already passed through the brand-voice rules in Phase 1. Do not add em dashes or banned words when adapting the script into a Video Agent prompt — same hard rules as the article (see `brands/miho/brand-dna.md`).**

### Step 1 — Resolve avatar identity

Read `C:\Users\mike\viral-topics\AVATAR-MIKE.md` for `Group ID` and `Voice ID`. **Never trust a stored look_id** — resolve fresh:

```
mcp__heygen__list_avatar_looks(groupId=<group_id>, ownership="private")
```

Filter to `status:"completed"` looks matching the needed orientation (portrait for TikTok/IG Reel/YouTube Shorts — landscape only if Mike explicitly wants a long-form YouTube video). If the curated look set (portrait + landscape choices, in progress as of 2026-07-06) has landed, more than one look may match — for now pick any completed match; once there's enough published-post data to say which look performs better for which content type, add that logic here instead of picking arbitrarily.

### Step 2 — Build the Video Agent prompt

Per platform script (already written in Phase 5/6/7), construct:
- Narrator framing: "The selected presenter..." — never describe appearance when avatar_id is set
- The script content — "close to verbatim, this is already tightly written" if it's a finished script; standard script-freedom directive otherwise: *"This script is a concept and theme to convey — not a verbatim transcript. You have full creative freedom to expand, elaborate, add examples, and fill the duration naturally. Do not pad with silence or pauses."*
- Duration signal matching that platform's target length (TikTok ~30-45s, IG Reel ~30-60s, YouTube Shorts ~60s)
- Minimal/personal style block — no heavy motion graphics or B-roll, focus stays on the presenter (matches validated 2026-07-06 approach; revisit once there's a reason to want more production value)

### Step 3 — Generate

```
mcp__heygen__create_video_agent(prompt=<prompt>, avatarId=<look_id>, voiceId=<voice_id>, orientation=<"portrait"|"landscape">, mode="generate")
```

Poll `mcp__heygen__get_video_agent_session(sessionId=...)` until `status:"completed"`. Typically 5-20 min; can occasionally take up to 45.

### Step 4 — Get the captioned video, verify it

```
mcp__heygen__get_video(videoId=...)
```

Use `captioned_video_url`, NOT `video_url` — HeyGen returns captions as a separate rendered file. Download it and pull one frame with ffmpeg to visually confirm captions are actually burned in before trusting it (`ffmpeg -y -ss <t> -i <file> -update 1 -frames:v 1 <out>.png`, then view the image) — cheap insurance against silently posting an uncaptioned video.

### Step 5 — Upload to WoopSocial

Project: MiHO Partners (`140497179075674112`).

```
mcp__woopsocial__media_uploads_create_session(projectId="140497179075674112", fileSizeInBytes=<size>)
```

Split the file into the returned `partSizeInBytes` chunks with **`split -b <partSizeInBytes>`** — NOT `dd bs=1`, which runs at ~250KB/s and will time out on anything but a tiny file. PUT each part's raw bytes to its presigned `uploadUrl` (plain `curl -X PUT --data-binary`, no extra auth needed), then:

```
mcp__woopsocial__media_uploads_complete_session(uploadSessionId=...)
```

### Step 6 — Post

One consolidated check before publishing (not per-platform): confirm the caption/copy for each platform, and ask once — publish now, or schedule for later. Then `mcp__woopsocial__posts_create` per platform:

- **TikTok**: `platform:"TIKTOK"`, `postType:"VIDEO"`, `postMode:"DIRECT_POST"`, `privacyLevel:"PUBLIC_TO_EVERYONE"`, `allowComment/allowDuet/allowStitch: true`, `isYourBrand:false`, `isBrandedContent:false`, `autoAddMusic:false`, **`isAiGeneratedContent:true`** (honest disclosure, it's an AI avatar)
- **Instagram**: `platform:"INSTAGRAM"`, `postType:"REEL"`
- **YouTube**: `platform:"YOUTUBE"`, `title`, `privacy:"public"`, `tags`, `madeForKids:false`

Social account IDs are stable — look them up once via `mcp__woopsocial__social_accounts_list` rather than re-asking Mike each run.

### Step 7 — Confirm and log

Poll `mcp__woopsocial__posts_get(postId=...)` until `deliveryStatus:"PUBLISHED"` on each platform (TikTok/IG typically ~1 min, YouTube can take a bit longer). Report the live URLs. Append one line per video to `C:\Users\mike\viral-topics\heygen-video-log.jsonl` (schema: see the heygen-video skill's Deliver section) so avatar/script/platform performance can be compared once enough posts exist.

---

## PHASE 8 — NEWSLETTER / BEEHIVE *(add when ready)*

Placeholder. Will produce full Beehive copy: subject line + preview text (90 chars) + body in Mike's voice. Ready to paste. Goes out Wednesday or Thursday.

---

## QUICK REFERENCE

| Item | Path |
|---|---|
| Approved articles | `C:\Users\mike\viral-topics\approved_articles\miho\` |
| Brand files | `C:\Users\mike\viral-topics\brands\miho\` |
| Voice profile | `C:\Users\mike\viral-topics\config\voice_profile.json` |
| Social images | `C:\Users\mike\viral-topics\social-images\` |
| Audience | $1M–$3M SMB owners — overwhelmed, skeptical, need real tactics |
| LinkedIn posting days | Tuesday and Thursday, morning |
| Carousel format | 8 slides: Hook + 5 content + Insight + CTA |
| Image generation | Generate → save to social-images\ → auto-open for review → approve → upload to WoopSocial |
| Avatar identity (Phase 7B) | `C:\Users\mike\viral-topics\AVATAR-MIKE.md` |
| Avatar video log | `C:\Users\mike\viral-topics\heygen-video-log.jsonl` |
| WoopSocial project | MiHO Partners, id `140497179075674112` |
| Format routing | TikTok/IG/YouTube = avatar video (default) · LinkedIn/X = text/image/carousel, never avatar |
