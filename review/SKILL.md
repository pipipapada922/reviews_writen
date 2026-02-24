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
- Keep language direct, natural, concise, and sharp.
- Keep tone objective, calm, grounded, and practical.
- Make the comments read like real X replies from a human perspective.
- In English, allow light human connectors when natural, such as well, honestly, or to be fair. Keep it subtle.

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
- Every key claim traces to a source or is marked uncertain.
- Every English comment is <= 280 characters.
- No generated comment contains quotation marks.
- Chinese translations preserve meaning and tone.
- Analysis is brief but interpretive, not a raw fact list.
- Wording is grounded, fluent, natural, and non-exaggerated.
