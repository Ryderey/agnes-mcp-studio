---
name: agnes-media-generation
description: Use only when the user explicitly mentions "agnes" (case-insensitive) and asks to generate, edit, combine, or animate images or videos with Agnes AI. Do not trigger for generic media generation without Agnes, media analysis, text generation, search, or live streaming.
---

# Agnes Media Generation

Use the `agnes_media` MCP server. If its tools are unavailable, ask the user to check the MCP configuration. Never activate without both the Agnes keyword and a media-generation intent.

## Workflow

1. Resolve the prompt language.
2. Select the narrowest matching tool.
3. Build a specific visual prompt and call the tool.
4. Present saved files and actionable errors.

## Tool selection

| Task | Tool | Key options |
|---|---|---|
| Standard image or image-to-image | `agnes_image_generate` | Exact-pixel `size`; optional `image_urls` |
| High-resolution image, wallpaper, poster | `agnes_image_generate_v2` | `size`=`1K`–`4K`; `ratio`; optional `image_urls` |
| Edit, restyle, or combine images | `agnes_image_edit` | One or more URL/local `image_paths` |
| Text-to-video | `agnes_video_generate` | Default all-in-one generation |
| Image-to-video | `agnes_video_generate` | Public `image` URL; `mode="ti2vid"` |
| Keyframe transition | `agnes_video_generate` | `mode="keyframes"`; URL array in `extra_body.image` |
| Async video or later polling | `agnes_video_submit` → `agnes_video_wait` / `agnes_video_status` | Preserve and report `video_id` |

Defaults: use `agnes_image_generate` at `1024x1024`; for requested high resolution use `_v2`, normally `2K` with the requested ratio. Use `agnes_video_generate` unless the user needs asynchronous progress or later retrieval.

## Prompt language

Resolve the mode from the current request, then an explicit earlier preference, otherwise use `auto`:

- `auto`: translate non-English prompts into natural English and optimize silently.
- `original`: optimize without changing language when the user asks to preserve it.
- `review`: show original and English versions and wait for selection when requested.

Preserve intent, proper nouns, numbers, camera directions, and quoted/on-screen text. Apply the same mode to `negative_prompt`. Use image prompts shaped as subject + scene + style + lighting + composition; use video prompts shaped as subject + action + scene + camera + lighting.

## Constraints and recovery

- Image inputs accept public HTTPS URLs, Data URIs, and local paths; video inputs require public HTTPS URLs.
- At 24 fps, video duration is limited to about 18 seconds. Let the MCP handle frame alignment and `response_format`.
- Mask-based editing is unsupported.
- On 429 or 503, wait and retry. On timeout, report `video_id` so polling can continue. For other errors, report the returned code and message.

## Output

- Show every generated image inline from its absolute `local_paths` entry.
- For video, provide `local_path` and `video_url` when available.
- Do not expose credentials or invent a successful result when a tool returns an error.
