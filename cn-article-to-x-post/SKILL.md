---
name: cn-article-to-x-post
description: Rewrite a Chinese article URL into publish-ready English X (Twitter) content in the style patterns of top AI/tech creators on X. Use when users ask to transform Chinese article links into English tweets/threads, request "X post/Twitter post" from a Chinese source, ask to "转写/改写成英文推文", or want high-engagement tech/AI social copy based on a Chinese article.
---

# CN Article To X Post

Convert a Chinese article link into concise, factual, high-engagement English X copy.
Mimic broad writing patterns from top AI/tech X creators without copying any individual wording.

## Workflow

1. Confirm input and output mode
- Require exactly one article URL.
- Default output: one main post plus one short thread.
- If user specifies only single-post or only thread, follow that.

2. Read and extract facts from the Chinese article
- Capture: core claim, what is new, supporting evidence, who it affects, and practical implication.
- Keep a fact list before writing copy.
- Do not invent numbers, claims, quotes, or timelines.

3. Search mentionable X accounts and verify handles
- Find 2-5 relevant accounts that can be safely mentioned, prioritizing official sources.
- Prefer official org/founder/media/project accounts directly tied to the article topic.
- Verify each handle before use; avoid ambiguous or fake handles.
- Include only accounts that add context value; do not force mentions.

4. Analyze current X style patterns (AI/tech)
- Review recent posts from leading AI/tech creators and summarize reusable style traits:
- short hook, clear POV, concrete takeaway, skimmable line breaks, direct CTA.
- Use style traits, never copy sentences verbatim.

5. Draft X-ready English outputs
- Create three hook options with different angles.
- Create one final main post (<= 280 chars).
- Create one thread with 3-6 replies (each <= 280 chars).
- Prefer sentence structures without colons whenever possible.
- Write thread replies as complete sentences and coherent short paragraphs, not fragments.
- Add relevant `@mentions` in main post and/or thread where natural.
- Append exactly 3 hashtags at the end of the main post and thread final reply.
- Create three optional CTA endings.

6. Quality check
- Verify all claims map back to extracted facts.
- Ensure fluent native English and X-native rhythm.
- Avoid overhype and generic buzzwords.
- Minimize colon usage across all outputs unless a colon is clearly necessary.
- Ensure comment-like thread replies read as full sentences with clear subject and verb.
- Keep exactly 3 hashtags total in each final publishable variant.
- Avoid hashtags/emojis unless user explicitly asks, except the mandatory 3 hashtags rule when requested.

## Output Template

Use this exact structure:

`Hook Options`
1) ...
2) ...
3) ...

`Main Post`
...

`Thread`
1/ ...
2/ ...
3/ ...

`CTA Options`
1) ...
2) ...
3) ...

`Mention Candidates`
- @handle1 (why relevant)
- @handle2 (why relevant)

## Guardrails

- Preserve meaning from the source Chinese article.
- If a fact is ambiguous, add one short `Assumption:` line before outputs.
- Do not present speculation as confirmed fact.
- Do not fabricate handles, partnerships, or endorsements.
- If no reliable mention target is found, explicitly state `No safe @mention found` and proceed without forced mentions.
