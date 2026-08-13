---
name: miho-blog-post
description: Publish a finished article to the MiHO Partners blog at mihopartners.com/insights. Use when the user says "publish this post", "put this on the blog", "post this to insights", "upload this article", "publish this to the site", or "/miho-blog-post". Takes finished writing in any format, converts it into the site's article format, checks it builds, pushes, and confirms it is actually live.
---

# miho-blog-post

Take a **finished** article and get it live at `mihopartners.com/insights/<slug>` — confirmed live, not just pushed.

## Scope — read this before anything else

**This skill only publishes.** It does not write, research, edit, or improve the article. If
the user hands you a draft and asks you to finish it, that is a different job — do that first
in a separate step, then come back here with the finished text.

**Input format does not matter, and is never the author's problem.** The article may arrive as
a markdown file, a plain `.txt`, pasted text in the conversation, a Google Doc export, the
output of some other writing skill, or a file with front matter in a completely different
shape. All of it is valid input. **This skill owns the entire translation** into the site's
article format.

Three rules that follow from that, and they are not negotiable:

1. **Never ask the author to reformat their writing.** If the input is missing something the
   site requires, you ask one short question or infer it — you do not send them away to fix
   their file.
2. **Never modify, depend on, or read the tool that produced the input.** Whatever skill,
   template, or app wrote the article is out of scope and stays untouched. Assume its output
   format will change without warning; this skill absorbs that.
3. **The site's format is the only contract that matters.** It lives in `post-format.md`
   next to this file. Read that file before writing any article file.

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

**2. Sync.** `git checkout main && git pull` in the working copy. Always, before writing
anything — otherwise the push conflicts.

**3. Convert the article.** Write `content/insights/<slug>.mdx` following `post-format.md`.
Derive what you can from the article itself (title, deck, date, slug, body). Ask only for what
you genuinely cannot infer — in practice that is almost always just **category**, because the
list is closed and guessing wrong fails the build. Ask for the whole set in one message, not
one question at a time.

**4. Check it builds — do not skip this.** The article's metadata is validated during the
build, and a bad value fails the whole build, which means the site stops updating for
everyone.

```
pnpm install
pnpm build
```

A build failure names the file and the exact problem. Fix it and build again. **Never push a
file that has not built cleanly.**

If `pnpm` or `node` is not installed on this machine, do not push to `main`. Instead push the
file to a new branch and open a pull request — the hosted preview build then acts as the gate,
and the user merges once it goes green.

**5. Commit and push.**

```
git add content/insights/<slug>.mdx
git commit -m "Insights: <article title>"
git push origin main
```

If the article includes an image, `git add` the image under `public/insights/` in the same
commit.

**6. Confirm it is live.** The deploy takes roughly a minute. Poll the real URL until it
returns 200, then give the user the link:

```
curl -s -o /dev/null -w "%{http_code}" https://mihopartners.com/insights/<slug>
```

Do not report success off a successful `git push`. A push is not a publish. If the URL is
still not 200 after about three minutes, say so plainly and point at the repo's Actions/deploy
status rather than claiming it worked.

## Failure modes worth knowing

- **`meta.category "..." is not one of:`** — the category is not in the closed list. Pick from
  the list in `post-format.md`; do not invent one and do not edit the site's category array to
  fit an article.
- **Build fails naming a file you did not touch** — someone else's post is broken, or the pull
  in step 2 was skipped. Pull and rebuild before assuming your file is the problem.
- **`content/insights/` must never be emptied.** The article route resolves posts by dynamic
  import and an empty directory fails the build outright. `_template.mdx` stays there
  permanently with `draft: true`. Never delete it.
- **Drafts.** `draft: true` means visible while developing, excluded from production, the
  listing and the sitemap. Publishing means `draft: false` or omitting the field. If the user
  wants to stage something without it going live, set `draft: true` and say so explicitly.
