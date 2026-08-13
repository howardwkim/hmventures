---
name: miho-blog-post
description: Publish, unpublish, or fix an article on the MiHO Partners blog at mihopartners.com/blog. Use when the user says "publish this post", "put this on the blog", "post this article to the blog", "upload this article", "take that post down", "unpublish that article", "remove that from the blog", "fix a typo on the blog", or "/miho-blog-post". Takes finished writing in any format, converts it into the site's article format, previews it, checks it builds, pushes, and confirms it is actually live. Not for social media — posting to LinkedIn, X, Instagram or TikTok is a different skill.
---

# miho-blog-post

Take a **finished** article and get it live at `mihopartners.com/blog/<slug>` — confirmed live, not just pushed.

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
   words that arrive are the words that ship. The one exception is escaping characters that
   would break the build (step 4) — that changes how a character is written, never what it says.
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
2. `~/src/hmventures/miho-landing-page/web`
3. Anywhere else the user names.

**If you use candidate 2, check where you are before any git command.** That directory is its
own repo *nested inside a different one* — its parent belongs to the `hmventures` repo, and
committing one directory too high puts the article in the wrong repository where it will never
deploy. Confirm both:

```
git rev-parse --show-toplevel   # must end in /web
git remote -v                   # must show miho-partners-landing, not hmventures
```

That copy is also often on a branch called `dev` rather than `main`. Step 2 handles it, but
tell the user you are moving their checkout and put it back when you're done.

### Cloning it the first time

```
gh repo clone howardwkim/miho-partners-landing ~/src/miho-partners-landing
```

Writing outside the current project may trigger a permission prompt the user has never seen
before. Say it's coming so it doesn't read as an error.

If `gh` isn't installed, or `gh auth status` says not logged in, **stop and ask the user to run
`gh auth login` in their own terminal** (GitHub.com → HTTPS → login with a web browser). It is
an interactive browser flow you cannot complete for them. **Never ask anyone to paste a token
or password into the chat.**

Three failures look similar and mean completely different things. Do not confuse them:

| What you see | What it means | What to say |
|---|---|---|
| `could not read Username for 'https://github.com': terminal prompts disabled` | Not authenticated at all. | Run `gh auth login` in your own terminal. |
| `Repository not found`, or a 404 on a repo that exists | Authenticated, but not yet a collaborator — **usually an invitation that was never accepted**. | Open https://github.com/howardwkim/miho-partners-landing/invitations and click Accept, or accept it from the GitHub email, then retry. Check that page before asking Howard for a new invite. |
| `remote: Permission to howardwkim/miho-partners-landing.git denied` (403 on push) | Read access only, or the invitation lapsed. | Ask Howard to confirm write access. |

## Steps

**0. Get the article.** "Publish this to the blog" often arrives with no file and no text. Ask
for the path or the text in one question, then proceed.

**1. Read `post-format.md`.** Every field rule, the closed category list, the body conventions,
the characters that break the build, and the slug rule are there. Do not work from memory.

**2. Sync, without disturbing the user's work.** Note the branch the working copy is currently
on and put it back there when you're done. If the tree is dirty, stop and say so rather than
stashing someone's uncommitted work behind their back. Then:

```
git checkout main && git pull
```

Always, before writing anything — otherwise the push conflicts.

**3. Ask the two things you cannot know, in one message.**

- **Who wrote it.** Required. This is a fact about the article, **not whose turn it is** —
  never infer it from the previous post, and never infer it from the template's default. It
  sets the byline name and photo, so getting it wrong publishes one partner's article under the
  other's face, and the build will not catch it. **This is the one place it is right to push
  back and insist on an answer.**
- **Which category.** The list is closed at five values; guessing wrong fails the build.
  Suggest the closest fit and let them confirm.

Then check the slug is free: `ls content/blog/`. If `<slug>.mdx` already exists, ask
whether this replaces that article or needs a different slug. **Never overwrite silently** — a
published URL can't be renamed without breaking every link to it.

**4. Convert the article.** Write `content/blog/<slug>.mdx` following `post-format.md`.
Set `draft: true` for now; step 5 flips it.

- **`date` is today's date**, not any date found in the author's file. A machine-written
  article often carries a stale one. Backdate only if the user asks.
- **Escape the two characters that break MDX.** A bare `<` and a bare `{` in ordinary prose
  will break the build — `post-format.md` has the rule and the exact error messages. Scan for
  them before writing. This is the only change you make to the author's text.
- **If there's an image:** create `public/blog/` if it doesn't exist, copy the file in, set
  `image` to `/blog/<filename>` and `imageAlt` to a real description. Then confirm the file
  landed (`ls public/blog/`) — only the alt text is build-enforced, so a missing image file
  builds clean and ships a broken picture. Most articles have no image; don't go looking.

**5. Show it before it goes live — this is the default path.** Publishing is a one-way door
for someone who doesn't use git, and a clean build only proves the metadata is valid, not that
the article reads right.

```
pnpm install --frozen-lockfile
pnpm dev
```

Drafts are visible in the local dev server and nowhere else. Give the user
`http://localhost:3000/blog/<slug>`, let them look, and wait for an explicit go. Then set
`draft: false`. Skip this only if they say to publish straight away.

**If `pnpm` is missing, install it** — don't route around it: `corepack enable && corepack
prepare pnpm@10 --activate`, or `npm install -g pnpm`. **If `node` is missing or older than
v20.9.0** (`node -v`), stop: Node has to come from [nodejs.org](https://nodejs.org) and you
cannot verify anything until it does. Do not push an unverified file to `main`. If the user
explicitly accepts publishing without a local check, push to a branch and run `gh pr create
--fill --base main`, hand them the pull request URL, and tell them plainly that you cannot
confirm the post went live.

**6. Check it builds — do not skip this.** The article's metadata is validated during the
build, and a bad value fails the whole build, which means the site stops updating for everyone.

```
pnpm build
```

A build failure usually names the file and the problem. Fix it and build again. **Never push a
file that has not built cleanly.**

Then confirm the article actually rendered, because a malformed `<Takeaway>` block does *not*
fail the build — it just comes out wrong:

```
pnpm start
curl -s localhost:3000/blog/<slug> | grep -c "What to do about it"
```

(Use the custom title if the article overrode it.) Stop the server afterwards.

Note the local Node version. Nothing in the repo pins it, and the hosting platform may build
with a different one — so a green local build is strong evidence, not a guarantee. Step 8 is
what actually confirms publication.

**7. Commit and push.**

First check there's a git identity, or the commit fails with `Author identity unknown` after
all the real work is done:

```
git config user.email
```

If it's empty, ask for the email on their GitHub account and set
`git config --global user.email "..."` and `git config --global user.name "..."`.

```
git add content/blog/<slug>.mdx
git commit -m "Blog: <article title>"
git push origin main
```

Include the image file in the same commit if there is one.

**8. Confirm it is live.** The deploy takes roughly a minute. Poll the real URL until it
returns 200, then give the user the link:

```
curl -s -o /dev/null -w "%{http_code}" https://mihopartners.com/blog/<slug>
```

Do not report success off a successful `git push`. A push is not a publish.

If it's still not 200 after about three minutes, say so plainly. **There is no GitHub Actions
workflow in this repo** — the deploy is Vercel's Git integration, so don't send anyone to an
Actions tab. Check the commit at
https://github.com/howardwkim/miho-partners-landing/commits/main for a deployment marker, and
if there's nothing after ~5 minutes, tell the user to ask Howard to check the Vercel dashboard.
Only he has access to it.

Then return the working copy to the branch it started on.

## Taking a post down, or fixing one

Same repo, same steps — the only thing that changes is what you write in step 4. There is no
separate admin panel, no content management system, and no dashboard anywhere in this. A post
is a file; changing the site means changing the file and pushing.

**To unpublish — the default, and what to reach for unless told otherwise.** Set `draft: true`
in the article's metadata block. It vanishes from production, from the `/blog` listing and
from the sitemap; its URL starts returning a genuine 404. The file stays in the repo, so the
article can be fixed and republished by flipping the flag back. Reversible both directions.

**To remove permanently.** Delete `content/blog/<slug>.mdx`. Same visible outcome, but the
text is gone from the working tree. Prefer `draft: true` unless the user explicitly wants the
file gone. Deleting every article is safe — the blog degrades to an empty listing rather
than breaking — but leave `content/blog/_template.mdx` alone anyway: it is the authoring
reference, not a post, and it never appears on the site.

**To fix a typo or change the wording.** Edit the file and push. The reader sees the corrected
version on the next deploy, about a minute later. There is no revision history to manage and
nothing to re-approve.

Whichever of the three it is: pull first, run the build, push, then confirm — for a takedown
the confirmation is the URL returning **404** and the article no longer appearing on
https://mihopartners.com/blog. Report the takedown only once you've seen that.

**Say this plainly if the user is anxious about it:** taking a post down is not a recall. If it
was live long enough for someone to read it or for a search engine to index it, removing the
file stops it being served but does not unsee it. Within a few minutes of publishing that is
almost never a real concern; a week later it might be.

## Two things about the site the author may not know

Mention these once, as information. Do not act on them — the article's content is the author's,
not yours.

- **The site appends its own call to action** to the bottom of every article. If the article
  already ends with one, the published page shows two. Say so and let the author decide.
- **There is no scheduling.** Nothing publishes itself at a future time. The honest equivalent
  is leaving the article as `draft: true` and pushing it live when the day comes.

## Failure modes worth knowing

- **`category "..." is not one of:`** — the category isn't in the closed list. Pick from
  the list in `post-format.md`; don't invent one and don't edit the site's category array to
  fit an article.
- **`Unexpected character ... before name`** at compile time — a bare `<` in the prose. See the
  MDX rules in `post-format.md`.
- **`ReferenceError: <word> is not defined`** during "Generating static pages" — a bare `{...}`
  in the prose. Same section. This one compiles clean and only dies at the very end, so it
  looks unrelated to the article.
- **Build fails naming a file you did not touch** — someone else's post is broken, or the pull
  in step 2 was skipped. Pull and rebuild before assuming your file is the problem.
- **Drafts.** `draft: true` means visible in the local dev server, excluded from production,
  the listing and the sitemap. Publishing means `draft: false` or omitting the field.
