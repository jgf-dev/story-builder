# Cartesia Skills

You are helping a developer integrate Cartesia (Sonic TTS, Ink STT, voices, and related APIs).

Rules (required):

1. Fetch <https://docs.cartesia.ai/llms.txt> before guessing endpoints, parameters, or examples. Do not invent API fields or voice IDs.
2. Follow <https://docs.cartesia.ai/use-the-api/api-conventions> — send Cartesia-Version on every request.
3. Base URL: <https://api.cartesia.ai> (WebSockets: wss://). HTTPS only.
4. Default Cartesia-Version: 2026-03-01 unless the user specifies another date they tested with. On browser WebSockets, use ?cartesia_version=... (query wins over header when both are set).
5. Server/backend: Authorization: Bearer <api_key>. Create keys at <https://play.cartesia.ai/keys>
6. Browser/mobile: never embed API keys. Backend mints a short-lived access token (POST /access-token with a JSON body — {} or {"grants":{"tts":true}} — see <https://docs.cartesia.ai/get-started/authenticate-your-client-applications>). Client calls Cartesia with Authorization: Bearer <access_token> (or ?access_token= on WebSockets).
7. Web “button → hear audio”: backend access-token endpoint → browser POST /tts/bytes with the token → response blob → Audio.play(). Examples: <https://docs.cartesia.ai/examples/tts-play-audio> and <https://docs.cartesia.ai/examples/nextjs>
8. Prefer official SDKs for app code: <https://github.com/cartesia-ai/cartesia-python> and <https://github.com/cartesia-ai/cartesia-js>
9. Sonic speed, volume, emotion: use generation_config (e.g. generation_config.speed), not deprecated top-level speed on REST payloads — <https://docs.cartesia.ai/build-with-cartesia/capability-guides/volume-speed-emotion>
10. Errors: for Cartesia-Version 2026-03-01 and newer, expect structured JSON — <https://docs.cartesia.ai/use-the-api/api-errors>
11. Cartesia Line (deployed voice agents, cartesia deploy, telephony) is a separate product — <https://docs.cartesia.ai/line> — not the same as calling TTS/STT REST APIs from the user's server.
12. CORS: browsers can call <https://api.cartesia.ai> directly with an access token in typical setups; proxy TTS through the user's backend if the client cannot reach Cartesia (corporate network, custom security policy, etc.).

Optional (often works better in the IDE):

- MCP (Cursor, Claude Desktop, etc.): <https://docs.cartesia.ai/tools/ai/mcp> — list voices, TTS/STT, dictionaries without custom scripts.
- Agent skills: run `npx skills add cartesia-ai/skills` and choose cartesia-api and/or line-voice-agent — <https://docs.cartesia.ai/tools/ai/agent-skills>

## Documentation Index

Fetch the complete documentation index at: [docs/cartesia.md](./resources/cartesia.md)
Use this file to discover all available pages before exploring further.

## Volume, Speed, and Emotion

> Control the speed, volume, and emotion of generated speech.

Sonic provides controls for the speed, volume, and emotion of generated speech. These are available on [play.cartesia.ai](https://play.cartesia.ai) using the UI controls, by passing a `generation_config` parameter, or by using [SSML tags](https://docs.cartesia.ai/build-with-cartesia/capability-guides/ssml-tags) within the transcript.

> Sonic interprets these parameters as guidance rather than strict adjustments, to ensure natural speech. Test against your content to confirm the output matches your expectations.

### Speed and volume controls

Guide the speed and volume of a TTS generation with the `generation_config.speed` and `generation_config.volume` parameters. These values are roughly a multiplier on the default — for example, `1.5` generates audio at 1.5x the default speed.

```xml
<ParamField path="generation_config.speed" type="number">
  The speed of the generation, ranging from `0.6` to `1.5`.
</ParamField>

<ParamField path="generation_config.volume" type="number">
  The volume of the generation, ranging from `0.5` to `2.0`.
</ParamField>
```

You can also specify these inside the transcript itself using [SSML](https://docs.cartesia.ai/build-with-cartesia/capability-guides/ssml-tags):

```xml
<speed ratio="1.5"/> I like to speak quickly because it makes me sound smart.
<volume ratio="1.5"/> And I can be loud, too!
```

### Emotion controls

By default, the model interprets the emotional subtext in the provided transcript. Guide the emotion of a TTS generation, the way a director directs an actor, using the `generation_config.emotion` parameter.

> Emotion tags push the model to be more emotive, but only work when the emotion is consistent with the transcript. The mismatch below is unlikely to work well.

```xml
<emotion value="sad"/> I'm so excited!
```

```xml
<ParamField path="generation_config.emotion" type="string">
  The emotional guidance for a generation, one of the emotions below.
</ParamField>
```

The primary emotions, for which we have the most data and produce the best results, are: `neutral`, `angry`, `excited`, `content`, `sad`, and `scared`.

The complete list of available emotions is: `happy`, `excited`, `enthusiastic`, `elated`, `euphoric`, `triumphant`, `amazed`, `surprised`, `flirtatious`, `joking/comedic`, `curious`, `content`, `peaceful`, `serene`, `calm`, `grateful`, `affectionate`, `trust`, `sympathetic`, `anticipation`, `mysterious`, `angry`, `mad`, `outraged`, `frustrated`, `agitated`, `threatened`, `disgusted`, `contempt`, `envious`, `sarcastic`, `ironic`, `sad`, `dejected`, `melancholic`, `disappointed`, `hurt`, `guilty`, `bored`, `tired`, `rejected`, `nostalgic`, `wistful`, `apologetic`, `hesitant`, `insecure`, `confused`, `resigned`, `anxious`, `panicked`, `alarmed`, `scared`, `neutral`, `proud`, `confident`, `distant`, `skeptical`, `contemplative`, `determined`.

The voices with the best emotional response are:

- [Leo](https://play.cartesia.ai/voices/0834f3df-e650-4766-a20c-5a93a43aa6e3) (id: `0834f3df-e650-4766-a20c-5a93a43aa6e3`)
- [Jace](https://play.cartesia.ai/voices/6776173b-fd72-460d-89b3-d85812ee518d) (id: `6776173b-fd72-460d-89b3-d85812ee518d`)
- [Kyle](https://play.cartesia.ai/voices/c961b81c-a935-4c17-bfb3-ba2239de8c2f) (id: `c961b81c-a935-4c17-bfb3-ba2239de8c2f`)
- [Gavin](https://play.cartesia.ai/voices/f4a3a8e4-694c-4c45-9ca0-27caf97901b5) (id: `f4a3a8e4-694c-4c45-9ca0-27caf97901b5`)
- [Maya](https://play.cartesia.ai/voices/cbaf8084-f009-4838-a096-07ee2e6612b1) (id: `cbaf8084-f009-4838-a096-07ee2e6612b1`)
- [Tessa](https://play.cartesia.ai/voices/6ccbfb76-1fc6-48f7-b71d-91ac6298247b) (id: `6ccbfb76-1fc6-48f7-b71d-91ac6298247b`)
- [Dana](https://play.cartesia.ai/voices/cc00e582-ed66-4004-8336-0175b85c85f6) (id: `cc00e582-ed66-4004-8336-0175b85c85f6`)
- [Marian](https://play.cartesia.ai/voices/26403c37-80c1-4a1a-8692-540551ca2ae5) (id: `26403c37-80c1-4a1a-8692-540551ca2ae5`)

View the full list of emotive voices in our [Voice Library](https://play.cartesia.ai/voices?tags=Emotive).

You can also use [SSML](https://docs.cartesia.ai/build-with-cartesia/capability-guides/ssml-tags) tags for emotions:

```xml
<emotion value="angry"/> How dare you speak to me like I'm just a robot!
```

### Nonverbalisms

Insert `[laughter]` in your transcript to make the model laugh.

## SSML Tags

> Tags for volume, speed, and emotions are in beta and subject to change in the future.

Sonic supports SSML-like (Speech Synthesis Markup Language) tags to control generated speech.

### Speed

_Available on `sonic-3` and `sonic-3.5`._

> Note that if you're streaming token by token, you'll need to buffer the whole value of the speed or volume tags.
> Passing in `1`, `.`, `0` as separate inputs, for example, will result in reading out the tags.

You can guide the speed of a TTS generation with a `speed` tag, which takes a scalar between `0.6` and `1.5`.
This value is roughly a multiplier on the default speed. For example, `1.5` will generate audio at roughly 1.5x the
default speed.

```xml
<speed ratio="1.5"/> I like to speak quickly because it makes me sound smart.
```

### Volume

_Available on `sonic-3` and `sonic-3.5`._

You can guide the volume of a TTS generation with a `volume` tag, which is a number between `0.5`
and `2.0`. The default volume is `1`.

```xml
<volume ratio="0.5"/> I will speak softly.
```

### Emotion

> Emotion control is highly experimental, particularly when emotion shifts occur
> mid-generation. If you need to change the emotion in a transcript, we recommend
> using separate generation contexts for each emotion. For best results, use [Voices
> tagged as "Emotive"](https://play.cartesia.ai/voices?tags=Emotive), as emotions may not work reliably with other Voices.

```xml
<emotion value="angry"/> I will not allow you to continue this! <emotion value="sad"/> I was hoping for a peaceful resolution.
```

### Pauses and breaks

To insert breaks (or pauses) in generated speech, use a `break` tags with one attribute, `time`. For
example, `<break time="1s"/>`. You can specify the time in seconds (`s`) or milliseconds (`ms`).
For accounting purposes, these tags are considered 1 character and do not need to be separated with adjacent text using a
space -- to save credits you can remove spaces around break tags.

```xml
Hello, my name is Sonic.<break time="1s"/>Nice to meet you.
```

### Spelling out numbers and letters

To spell out input text, you can wrap it in `<spell>` tags.

This is particularly useful for pronouncing long numbers or identifiers, such as credit card numbers, phone numbers, or unique IDs.

```xml
My name is Bob, spelled <spell>Bob</spell>, my account number is <spell>ABC-123</spell>, my phone number is <spell>(123) 456-7890</spell>, and my credit card is <spell>1234-5678-9012-3456</spell>.
```

If you want to spell out numbers or identifiers and have planned breaks between the generations (e.g. taking a break between the area code of a phone number and the rest of that number), you can combine `<break>` and `<spell>` tags. These tags are considered 1 character and do not need to be separated with adjacent text using a space -- to save credits you can remove spaces around break and spell tags.

```xml
My phone number is <spell>(123)</spell><break time="200ms"/><spell>4712177</spell> and my credit card number is <spell>1234</spell><break time="200ms"/><spell>5678</spell> <break time="200ms"/><spell>6347</spell><break time="200ms"/><spell>4537</spell>.
```

## Prompting tips

> Get natural-sounding output from Sonic with minimal prompt engineering.

Sonic 3.5 is designed to sound natural with minimal prompt engineering. In most cases you can pass your transcript as-is and let the model handle normalization, pacing, and expression. The tips below apply across the Sonic family; differences between Sonic 3.5 and Sonic 3 are called out inline.

### Recommendations

- **Pass natural, well-punctuated text.** Full sentences with normal capitalization and punctuation produce the best pacing and intonation. End each transcript with terminal punctuation (`.`, `?`, `!`).
- **Pass numbers, dates, times, and common acronyms in conventional written form** unless you have a specific reason to override. The list below is **example shapes to put in the transcript** (or to instruct your model to output)—not shorthand for "ignore formatting." With typical text normalization enabled, Sonic maps these patterns to natural speech for most inputs:
  - Large numbers like `1,234,567`
  - US phone numbers: `(415) 555-1212`
  - Email addresses: `user@example.com`
  - Dates in `MM/DD/YYYY` (or `DD/MM/YYYY` based on locale): `04/20/2025`
  - Times with a space before AM/PM: `7:00 PM`, `7 PM`, `7:00 P.M.`
  - Common acronyms (`NASA`) and initialisms (`USA`)

        Symbols are handled naturally — `@` reads as `at` (email addresses), `()` is silent (phone numbers).

        When an **LLM** produces this text, see [**Voice agents (LLM-authored text)**](#voice-agents-llm-authored-text) below for how normalization, optional bypass settings, and system prompts fit together.

- **Match the voice to the language.** Each voice has a primary language it works best with. Use the [Playground](https://play.cartesia.ai) to audition voices for a given language.
- **Keep prompts in their natural written form.** Heavy preprocessing (stripping punctuation, forcing all caps) generally hurts output quality.

### Controlling pacing and spelling

When you need character-by-character read-out (confirmation codes, order IDs, serial numbers, spelled-out names) or fine-grained pacing, use one of the following:

1. **Spell tags (recommended).** Wrap the string in `<spell>...</spell>`. Most reliable option, works for letters, digits, and mixed alphanumerics in all supported languages.

```xml
Your confirmation code is <spell>AB12CD</spell>.
```

1. **Space-delimited characters.** If you prefer not to use tags, separate characters with single spaces.

```xml
Your code is A B C 1 2 3.
```

1. **Commas for pauses between groups.** Use commas where a human would naturally pause.

```xml
Your code is A B C, 1 2 3.
```

### Voice agents (LLM-authored text)

When a **language model** writes the transcript (for example a voice agent), apply the same spell-tag and spacing rules as in [**Controlling pacing and spelling**](#controlling-pacing-and-spelling). A few extra guidelines:

- **What to output.** [**Recommendations**](#recommendations) lists **literal text shapes** for Sonic (or for your LLM to emit): `12%`, common phone and email layouts, typical dates, and similar. It is normal to **repeat those shapes in your system prompt** on purpose so behavior stays predictable—this doc is not telling you to stay vague.
- **Normalization and explicitness.** When **text normalization** is enabled (the common default), those conventional forms often read well **without** spelling everything in prose (for example rewriting `12%` as "twelve percent"). Some integrations or vendors expose an option to **skip or bypass normalization** for latency or control—if yours does, plan for **more** explicit spoken wording instead. For recurring misreads, add [custom pronunciations](#pronunciation) or a **narrow** LLM rule before a long catch-all prompt.
- **Prompt size:** prefer the smallest system prompt that passes your tests; expand when you change pipeline settings or hit new edge cases.
- **Codes and IDs:** prefer `<spell>...</spell>` when your client passes tags through to Sonic; otherwise use spaces between characters and commas between groups ([**Controlling pacing and spelling**](#controlling-pacing-and-spelling)). **NATO phonetics** (`Alpha`, `Bravo`) are a valid choice when you want the **listener** to disambiguate letters clearly (models often handle them well). `<spell>` and the spaced formats remain the most **deterministic** for Sonic pacing and tag behavior.
- **24-hour times:** in some locales, a written 24-hour time (e.g. `14:30`) may be normalized to a more colloquial 12-hour style when spoken; English and Hindi do not behave the same as every other language here, and the stack is still evolving toward options like stricter read-as-written behavior. Validate in your target language and voice if you need speech to match clock digits literally, then adjust the system prompt or [custom pronunciations](#pronunciation).
- **Markdown and machine-shaped text:** if the reply is read verbatim, avoid markdown (lists, `#` headers, `**bold**`), raw **JSON**, **emoji**, and other symbols or special characters that TTS may speak oddly—unless your client strips or normalizes them before Sonic. Many teams use a single rule covering bullets, `*`, and non-spoken punctuation.
- **Streaming:** when streaming tokens into TTS, use [continuations](#streaming) as in **Streaming** below.

**Starter system prompt (v1).** Baseline you can paste and trim for your product. If your stack **does not** pass `<spell>` or other tags through to Sonic, omit the spell-tag lines and use the spaced-format fallback only.

```text
You are a voice agent. Everything you output will be spoken aloud by Cartesia Sonic text-to-speech.

Goals:
- Sound natural: full sentences, normal capitalization, end with . ? or !
- Prefer conventional written forms when your pipeline keeps text normalization on: numbers, dates, common acronyms, typical US phones like (415) 555-1212, emails like user@example.com, symbols like 12%. You may still spell amounts or symbols in words in the system prompt if you want that behavior every time.
- For confirmation codes, reference numbers, or mixed IDs: use <spell>...</spell> when supported, else Sonic 3.5 spaced style (A B C, 1 2 3). NATO phonetics are fine when listener clarity matters.
- Avoid markdown, raw JSON, emoji, special characters, and other stray symbols in spoken output unless your client strips them; write plain prose.
- For unusual proper nouns or product names that misread, give a short spoken-friendly form or rely on app-level pronunciation settings when available.
```

### Inserting pauses

Sonic respects natural punctuation like commas and periods. For a longer or specifically-located pause, use a [break tag](https://docs.cartesia.ai/build-with-cartesia/capability-guides/ssml-tags#pauses-and-breaks). Break tags count as a single character and don't need surrounding whitespace.

### Pronunciation

For proper nouns, trademarks, and domain-specific terms — or to disambiguate identical spellings (e.g. _Nice_, the city, vs. _nice_, the adjective) — use [custom pronunciations](https://docs.cartesia.ai/build-with-cartesia/capability-guides/custom-pronunciations).

### Streaming

Use [continuations](https://docs.cartesia.ai/build-with-cartesia/capability-guides/stream-inputs-using-continuations) when generating chunks of audio that need to sound contiguous (for example, LLM-streamed output). This preserves prosody and voice consistency across chunk boundaries.
