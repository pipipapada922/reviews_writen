---
name: review
description: Verify and deconstruct X (Twitter) posts before drafting bilingual comments. Use when the user provides an X post URL and asks for background search, factuality and recency checks, exaggeration/marketing analysis, and English comments (max 280 chars) with Chinese translations in specific styles.
---

# Review

## Core Goal

Produce evidence-based X comments with a short Chinese content deconstruction first.

## Required Workflow

Follow these steps in order.

1. Parse and fetch the source post.
- Accept an X status URL or pasted post text.
- Try direct page read first.
- If direct read fails, use X syndication fallback:
  - Endpoint: `https://cdn.syndication.twimg.com/tweet-result?id={status_id}&token={token}`
  - Use a deterministic token derived from status id (same method used in prior successful fallback in this environment).
- If both fail, ask the user to paste the post content and continue.

2. Search background and verify claims.
- Search for primary sources first: official docs, papers, institutions, regulator or company statements, reputable outlets.
- Check whether the post is recent and relevant to current timeline.
- Identify whether claims are accurate, outdated, incomplete, marketing-heavy, or exaggerated.
- Flag uncertainty explicitly. Do not guess.
- Use lightweight comparative verification first. Prioritize major factual direction and key numbers.
- Do not over-focus on wording nuances unless the claim is high-risk, clearly misleading, or materially changes meaning.

3. Write a short Chinese deconstruction, not only fact-checking.
- Cover these points in plain language:
  - What is factually supported.
  - What could be over-interpreted.
  - What the post is trying to frame.
  - `可以理解为...`
  - `可能和...有关`
  - `关于这个话题，人们关心的点在于...`

4. Draft bilingual comments.
- Write English comments first.
- Under each English comment, add a Chinese translation.
- Keep each English comment under 280 characters.
- Do not use quotation marks in generated comments.
- Do not use colons in generated comments.
- Keep normal punctuation in all other cases. Do not remove natural punctuation marks.
- Keep language direct, natural, concise, and sharp.
- Keep tone objective, calm, grounded, and practical.
- Make the comments read like real X replies from a human perspective.
- In English, allow light human connectors when natural, such as well, honestly, or to be fair. Keep it subtle.
- Avoid heavy technical jargon. Write like a native social media user.
- Integrate facts into opinion directly. Do not sound like an editor doing line-by-line correction.
- Avoid inflated big words and hype framing.

## Comment Style Requirements

Generate comments across these styles:
- Fact-checking.
- Science explainer.
- Content correction.
- Real-life application.

Additional constraints:
- Sound fluent and native, not robotic.
- Avoid dramatic or exaggerated wording.
- Avoid heavy metaphors and decorative phrasing.
- Prefer verifiable details when available: date, location, mission, paper, official source.
- Keep wording simple enough for general social media readers.
- Express views directly and naturally instead of correction-style commentary.
- Avoid quotation marks and colons in generated comments.
- Normal punctuation is allowed and encouraged for readability.
- If the content of the post is basically correct and no suspicion of exaggeration, do not deliberately deny or find fault

## Output Format

Use this structure unless the user asks otherwise.

```text
[内容分析]
- ...
- ...
- 可以理解为...
- 可能和...有关
- 关于这个话题，人们关心的点在于...

[评论方案]
Comment 1（事实核查版）:
<EN <= 280>
CN:
<中文翻译>

Comment 2（科普版）:
<EN <= 280>
CN:
<中文翻译>

Comment 3（内容矫正版）:
<EN <= 280>
CN:
<中文翻译>

Comment 4（生活落地版）:
<EN <= 280>
CN:
<中文翻译>

Sources:
- <url>
- <url>
```

## Quality Checks

Before finalizing, ensure:
- Every English comment is <= 280 characters.
- No generated comment contains quotation marks or colons.
- Other punctuation remains natural and readable.
- Chinese translations preserve meaning and tone.
- Analysis is brief but interpretive, not a raw fact list.
- Wording is grounded, fluent, natural, and non-exaggerated.
- Comments do not read like technical copy editing or fact-check reports.
