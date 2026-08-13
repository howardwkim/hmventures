---
name: miho-blog-post
description: Publish, unpublish, or fix an article on the MiHO Partners blog at mihopartners.com/insights. Use when the user says "publish this post", "put this on the blog", "post this article to insights", "upload this article", "take that post down", "unpublish that article", "remove that from the blog", "fix a typo on the blog", or "/miho-blog-post". Takes finished writing in any format, converts it into the site's article format, previews it, checks it builds, pushes, and confirms it is actually live. Not for social media — posting to LinkedIn, X, Instagram or TikTok is a different skill.
---

# miho-blog-post

Take a **finished** article and get it live at `mihopartners.com/insights/<slug>` — confirmed live, not just pushed.

## Scope — read this before anything else

**This skill only publishes.** It does not write, research, edit, or improve the article. If
the user hands you a draft and asks you to finish it, that is a different job — do that first
in a separate step, then come back here with the finished text.

**Input format does not matter, and is never the author's problem.** The article may arrive as
a markdown file, a plain `.txt`, pasted text in the conversation, a document export, or a file
with metadata in a completely different shape. All of it is valid input. **This skill owns the
entire translation** into the site's article format.

Four rules that follow from that, and they are not negotiable:

1. **Never ask the author to reformat their writing.** If the input is missing something the
   site requires, you ask one short question or infer it — you do not send them away to fix
   their file.
2. **Never change the author's words.** You reshape *metadata and structure* — the title into
   the title field, headings down a level, a summary line into the deck. You do not rewrite,
   trim, tighten, delete paragraphs, or improve the prose, even when it looks improvable. The
   words that arrive are the words that ship.
3. **Stay independent of whatever produced the article.** Do not read, reference, depend on,
   or modify the tool, template, or app that wrote it. Assume its output format changes
   without warning; this skill absorbs that silently. Nothing here should ever need updating
   because something upstream changed.
4. **The site's format is the only contract that matters.** It lives in `post-format.md` next
   to this file. Read that file before writing any article file.

## Where the site lives

Private repo: `https://github.com/howardwkim/miho-partners-landing` (default branch `main`).
Pushing to `main` deploys to production automatically. Nobody needs a Vercel account —
the deploy runs on the repo owner's Vercel project, triggered by the push alone.

Find the working copy in this order:

1. `~/src/miho-partners-landing`
2. `~/src/hmventures/miho-landing-page/web` (this is where it sits for Howard, nested inside
   the hmventures workspace)
3. Anywhere else the user names.

If none exists, clone it:

```
git clone https://github.com/howardwkim/miho-partners-landing.git ~/src/miho-partners-landing
```

If the clone fails with a permission or 404 error, the account is not a collaborator on the
private repo yet. Stop and say exactly that — it is an access problem, not a git problem, and
the fix is an invitation from Howard, not a retry.

## Steps

**1. Read `post-format.md`.** Every field rule, the closed category list, the body
conventions and the slug rule are there. Do not work from memory.

**2. Sync, without disturbing the user's work.** Note the branch the working copy is currently
on before you touch anything, and put it back there when you're done. If the tree is dirty,
stop and say so rather than stashing someone's uncommitted work behind their back. Then:

```
git checkout main && git pull
```

Always, before writing anything — otherwise the push conflicts.

**3. Ask the two things you cannot know, in one message.**

- **Who wrote it.** Required, and it is the one field nothing in the article implies. It sets
  the byline name and photo, so guessing wrong publishes one partner's article under the
  other's face, and the build will not catch it. Propose a default rather than asking cold:
  read the `author` of the most recent published post and offer the other one, since articles
  are meant to alternate. **This is the one place it is right to push back on the author and
  insist on an answer.**
- **Which category.** The list is closed at five values; guessing wrong fails the build.
  Suggest the closest fit and let them confirm.

Everything else — title, deck, date, slug, body — comes from the article itself.

**4. Convert the article.** Write `content/insights/<slug>.mdx` following `post-format.md`.
Set `draft: true` for now; step 5 flips it.

If the article came with an image: create `public/insights/` if it does not exist, copy the
image in named after the slug, set `image` to `/insights/<slug>.<ext>`, and write a real
`imageAlt` describing what the image shows — a missing or empty alt fails the build. Articles
with no image are the normal case; do not go looking for one.

**5. Show it before it goes live — this is the default path.** Publishing is a one-way door
for someone who does not use git, and a successful build only proves the metadata is valid,
not that the article reads right.

```
pnpm install
pnpm dev
```

Drafts are visible in the local dev server and nowhere else. Give the user
`http://localhost:3000/insights/<slug>`, let them look, and wait for an explicit go. Then set
`draft: false`.

Skip this only if the user explicitly says to publish straight away.

If `pnpm` or `node` is not installed on this machine, you cannot preview or build locally.
Push the file to a new branch and open a pull request instead — the hosted preview build then
serves as both the preview and the gate, and the user merges it when they're happy.

**6. Check it builds — do not skip this.** The article's metadata is validated during the
build, and a bad value fails the whole build, which means the site stops updating for
everyone.

```
pnpm build
```

A build failure names the file and the exact problem. Fix it and build again. **Never push a
file that has not built cleanly.**

**7. Commit and push.**

```
git add content/insights/<slug>.mdx
git commit -m "Insights: <article title>"
git push origin main
```

Include the image file in the same commit if there is one.

**8. Confirm it is live.** The deploy takes roughly a minute. Poll the real URL until it
returns 200, then give the user the link:

```
curl -s -o /dev/null -w "%{http_code}" https://mihopartners.com/insights/<slug>
```

Do not report success off a successful `git push`. A push is not a publish. If the URL is
still not 200 after about three minutes, say so plainly and point at the repo's deploy status
rather than claiming it worked.

Then return the working copy to the branch it started on.

## Taking a post down, or fixing one

Same repo, same steps — the only thing that changes is what you write in step 4. There is no
separate admin panel, no content management system, and no dashboard anywhere in this. A post
is a file; changing the site means changing the file and pushing.

**To unpublish — the default, and what to reach for unless told otherwise.** Set `draft: true`
in the article's metadata block. It vanishes from production, from the `/insights` listing and
from the sitemap; its URL starts returning 404. The file stays in the repo, so the article can
be fixed and republished later by flipping the flag back. Reversible in both directions.

**To remove permanently.** Delete `content/insights/<slug>.mdx`. Same visible outcome, but the
text is gone from the working tree. Prefer `draft: true` unless the user explicitly wants the
file gone — and never delete the last article in the directory (see the failure modes below).

**To fix a typo or change the wording.** Edit the file and push. The reader sees the corrected
version on the next deploy, about a minute later. There is no revision history to manage and
nothing to re-approve.

Whichever of the three it is: pull first, run the build, push, then confirm — for a takedown
the confirmation is the URL returning **404**, and the article no longer appearing on
`https://mihopartners.com/insights`. Report the takedown only once you've seen that.

**Say this plainly if the user is anxious about it:** taking a post down is not a recall. If it
was live long enough for someone to read it or for a search engine to index it, removing the
file stops it being served but does not unsee it. Within a few minutes of publishing that is
almost never a real concern; a week later it might be.

## Two things about the site the author may not know

Mention these once, as information. Do not act on them — the article's content is the author's,
not yours.

- **The site appends its own call to action** to the bottom of every article. If the article
  already ends with one, the published page will show two. Say so and let the author decide.
- **There is no scheduling.** Nothing publishes itself at a future time. The honest equivalent
  is leaving the article as `draft: true` and pushing it live when the day comes.

## Failure modes worth knowing

- **`meta.category "..." is not one of:`** — the category is not in the closed list. Pick from
  the list in `post-format.md`; do not invent one and do not edit the site's category array to
  fit an article.
- **Build fails naming a file you did not touch** — someone else's post is broken, or the pull
  in step 2 was skipped. Pull and rebuild before assuming your file is the problem.
- **`content/insights/` must never be emptied.** The article route resolves posts by dynamic
  import and an empty directory fails the build outright. `_template.mdx` stays there
  permanently with `draft: true`. Never delete it.
- **Drafts.** `draft: true` means visible in the local dev server, excluded from production,
  the listing and the sitemap. Publishing means `draft: false` or omitting the field.
