---
name: tts-prompt-generation-and-splitting
title: "Gemini Text-to-Speech Prompt Generator"
description: End-to-end workflow for converting a raw story markdown file into structured, annotated TTS prompts with emotional cues and voice personas, chunked to comply with the 2-voice API limit.
---

<!-- @format -->

## TTS Prompt Generation Workflow

Converting a raw story into structured TTS prompts involves a creative annotation phase (assigning voices, adding emotion tags) followed by a mechanical splitting phase (chunking the transcripts to respect the Google GenAI TTS 2-voice limit).

This skill documents the repeatable, end-to-end process for taking a raw story file (e.g., `story.md`) and producing a sequence of API-ready scene prompt files.

### Step 1: Analyze the Source Material

1. **Read the story:** Read the raw story file to understand the characters, tone, and narrative arc.
2. **Review TTS Guidelines:** Read the **Gemini Text-to-Speech Guidelines** section below to understand the required prompt schema (`Audio Profile`, `Scene`, `Director's Notes`, `Sample Context`, `Transcript`) and the available voice options.
3. **Outline Scenes:** Break the story down logically into major scenes or chapters.

### Step 2: Generate the Initial Scene Prompts

For each identified scene, generate a structured markdown file (named using the glob pattern `*-scene*.md`, e.g., `01-scene1.md`, `02-scene2.md`).

**Important:** Do not worry about the 2-voice limit in this step. Focus on the narrative flow, maintaining continuity, and correctly annotating the entire scene.

Each scene file must strictly follow this structure:

```markdown
# SYSTEM PREAMBLE: Synthesize speech ONLY for the transcripts under the #### TRANSCRIPT headers. Do NOT read aloud the section titles, scene descriptions, actor names, or director notes.

# AUDIO PROFILE: [Scene Title]

## "[Subtitle]"

### THE SCENE: [Location]

[Description of the physical scene and atmosphere, focusing on physical proximity, lighting, and acoustic environment]

### DIRECTOR'S NOTES

Style:

- [Character1] (Voice: [VoiceName]): [Description of character's voice, delivery style, projection level, and proximity]
- [Character2] (Voice: [VoiceName]): [Description of character's voice, delivery style, projection level, and proximity]
  ...

Pace: [Description of pacing]
Accent: [Description of accents]

### SAMPLE CONTEXT

[Summary of what is happening in this scene]

#### TRANSCRIPT

Character1: Dialogue text...
Character2: Dialogue text...
Character1: [emotion_tag] More dialogue...
```

> [!IMPORTANT]
> The `# SYSTEM PREAMBLE` line is **mandatory** in every prompt file. Without it, the model may read aloud the section titles, scene descriptions, and director notes instead of treating them as stage directions. This is the single most common cause of `PROHIBITED_CONTENT` rejections and instructions being spoken aloud.

**Rules for the emotion_tag:**

- **IF** the character is speaking (as opposed to narrator)
- The tag should be a single word or short phrase enclosed in square brackets.
- Use tags sparingly. They will significantly impact the generated voices and delivery. They can quickly make the voices sound ridiculous.
- A shouting tag **will** make the character **shout loudly**, for the entire sentence. Whispering tags make the voices barely audible.
- Do not include a tag for every line in the transcript. Only include tags for lines where you want to change the delivery of the line.
- To moderate the level of emotion, use dampening modifiers like "more ", "less " and "normal" before the tag, e.g. [more excited], [less sad], [normal breathing].
- **NEVER** place two audio tags directly adjacent to each other (e.g., `[sighs][whispers]`). This causes a system parsing error. Always separate them with a space, punctuation, or dialogue text (e.g., `[sighs] [whispers]` or `[sighs], [whispers]`).
- Tags must always be in **English**, even if the surrounding spoken text is in another language.
- **Voice-specific behavior**: The voice you choose and its training samples will affect tag effectiveness. Some tags work well with certain voices but may sound unnatural with others. Iterate and regenerate as needed.

**Intimacy Scene Tag Restrictions:**

During intimate or erotic scenes, restrict the tag palette to the curated "Intimacy Palette" listed in the M4M Guidelines section below. Specifically:

- ❌ **NEVER** use during intimate scenes: `[shouting]`, `[excited]`, `[anger]`, `[frustration]`, `[determination]`, `[loud]`. These render as jarring, high-energy delivery that instantly breaks immersion.
- ❌ **Avoid** melodramatic or theatrical tags. High-pitched excitement or theatrical sadness sounds cartoonish and destroys the intimate atmosphere.
- ✅ **Use instead**: `[whispers]`, `[sighs]`, `[gasp]`, `[adoration]`, `[tension]`, `[nervousness]`, `[trembling]`, `[short pause]`, `[medium pause]`, `[long pause]`.

**Rules for the Transcript:**

- Every line must start with `CharacterName:`.
- All narrative, non-dialogue lines must be explicitly attributed to a specific narrator character.
- **NEVER** place dialogue and narration on the same line. If a character speaks and then there is narration, they must be split into two separate lines with their respective character prefixes.
- **ALWAYS** retain quotation marks (`"`) around spoken dialogue to ensure the TTS model inflects it as speech rather than thought/narration.

**"One Breath Per Line" Formatting Rule:**

Structure the transcript so that each line represents roughly one breath of speech. Shorter phrases divided by physical line breaks naturally signal the TTS model to introduce breathing intervals, preventing the rushed, breathless reading typical of older text-to-speech engines.

- Write shorter dialogue blocks rather than dense paragraphs.
- Separate emotionally distinct beats onto their own lines.
- As a general pacing benchmark, 100 words of script equates to approximately one minute of final audio. Do not over-pack transcripts with text; allow the atmosphere, audio tags, and pauses to do the heavy lifting.

### Step 3: Run the Splitter Script

The Google GenAI TTS API enforces a limit of a maximum of 2 distinct voices per API call.
Once you have generated the annotated `*-scene*.md` files, you must use the provided Python script to automatically chunk them.

The script iterates through the transcripts line-by-line and breaks them into sequentially numbered `XX-part.md` files anytime a third unique speaker is introduced.
It also dynamically reconstructs the `Style:` section for each new chunk so it only contains the voices actively used in that file.

> [!NOTE]
> The text-to-speech generation process is built on the `client.interactions` API, which maintains stateful conversational context between chunks by passing the previous interaction ID.
> This allows the model to naturally carry over emotional flow, volume, and pacing from the previous scene boundary.
> However, to ensure maximum stability and prevent characteristics from drifting, you MUST still repeat fixed and persistent character characteristics (assigned voices, accents, personalities, tones) in the `Style:` section of every prompt chunk.

#### Execution

Run the script from the terminal, passing the directory containing your generated `*-scene*.md` files:

```bash
python .agent/skills/tts-prompt-crafter/scripts/split_prompts.py <path-to-prompts-directory>
```

**Example:**

```bash
python .agent/skills/tts-prompt-crafter/scripts/split_prompts.py .agent/skills/google-genai-sdk/example
```

### Step 4: Verification

1. Verify that the original `*-scene*.md` files have been removed by the script.
2. Check the output directory for the sequentially numbered chunk files (`01-part.md`, `02-part.md`, etc.).
3. Ensure no single output file contains more than two distinct voices in its `Style:` section.

The resulting files are now fully compliant and ready to be processed sequentially by the TTS API.

## Prompting Guide for Controllable Speech

The **Gemini Native Audio Generation Text-to-Speech (TTS)** model differentiates itself from conventional engines by utilizing a large language model that knows not only _what_ to say, but _how_ to say it. The prompt acts as a set of system instructions and stage directions. By structuring the prompt with specific markdown headers, you control the character's voice profile, environment, and delivery style.

### 1. The Canonical Prompt Structure

To ensure predictable results and prevent the model from reading director's notes or scene headings aloud, you must adhere to a strict, delimited structure and include a mandatory system preamble at the start of the file.

- **System Preamble**: An explicit, clear instruction telling the model to synthesize speech _only_ for the transcript and to ignore headings, profiles, and stage directions.
- **AUDIO PROFILE**: Defines the persistent identity of the speaker(s).
- **THE SCENE**: Establishes the physical space, lighting, acoustic properties, and emotional atmosphere.
- **DIRECTOR'S NOTES**: Technical guidelines for voice quality, pacing, accent, and consistency.
- **TRANSCRIPT**: The actual spoken text, isolated by a hard boundary (`#### TRANSCRIPT`).

### 2. General Phrasing & Punctuation Rules

- **Delimiters**: Always use the `#### TRANSCRIPT` header as a strict partition.
- **Punctuation**: Avoid writing short sentence fragments separated by periods, as the model will pause aggressively, leading to a choppy, robotic cadence. Instead, use commas, dashes, and ellipses (`...`) to guide smooth, natural phrasing.
- **Consistency Directive**: In `DIRECTOR'S NOTES`, explicitly state consistency bounds to keep the voice stable across lines, e.g., _"Maintain 85% voice identity polish, 15% emotional range."_

---

## Acoustic Intimacy & Erotic Audio Principles

Intimate or erotic audio storytelling relies on creating a "cocoon of privacy" between the voice and the listener. The vocal performance must transition from public speech to close-up, biological communication. Human listeners possess highly attuned evolutionary filters that quickly identify synthetic voices lacking natural physical reactions—hesitations, breath variations, or subtle vocal fatigue. Overcoming the "uncanny valley" in intimate audio means understanding and manipulating the physics of sound capture and human vocal anatomy.

### 1. The Proximity Effect (The Bass Boost)

The proximity effect is an acoustic phenomenon that amplifies low-frequency resonance when a sound source (the human voice) is placed extremely close to a directional microphone. This isolates the voice, creating a heavy, deep, and rich foundation that makes the listener feel as though the speaker is literally inside their personal space.

- **Prompting**: Direct the model to simulate an _“extreme microphone proximity (proximity effect)”_ in the `Style:` notes. This prompts the model to boost low-end registers and capture microscopic biological textures like lip smacks and breath.

### 2. Glottal Flow & the "Bedroom Voice"

True intimacy is rarely loud; it relies on turbulent airflow. A seductive or vulnerable voice occurs when the vocal folds fail to close completely, allowing a steady, highly audible stream of hissing air to mix with the fundamental tone (glottal flow). This breathiness signals a shift from public, performative speech to private, relaxed, or aroused communication. If the TTS model is not explicitly directed to introduce this breathiness, it will default to a clear, firm articulation that feels clinical.

- **Prompting**: Instruct the model to speak with _"high breathiness and glottal flow."_ Whispering should be used selectively (using inline `[whispers]` tags) rather than continuously, as continuous whispering sounds artificial and lacks emotional depth.
- **Raised soft palate**: For a softer, more intimate resonance without sharp volume, instruct the model to use a _"raised soft palate."_ This lifts the velum at the back of the roof of the mouth, brightening vocal resonance and introducing a subtle "vocal smile" while reducing harsh nasal turbulence.

### 3. Pacing and Strategic Silence (ASMR)

A common error is the assumption that continuous, rapid speech equates to high engagement. In reality, intensity of emotion is not synonymous with intimacy—genuine intimacy requires deliberate time to develop, both emotionally and acoustically. Silence is where tension and arousal build.

- **Prompting**: Direct the model to use _"slow, measured, ASMR-like pacing (around 0.7x to 0.8x normal conversational speed)"_.
- **Transcript Pauses**: Embed `[short pause]`, `[medium pause]`, or `[long pause]` inline tags between clauses—not just between sentences. Insert pauses between _words_ to simulate a speaker who is physically overwhelmed or distracted.
- **Non-Verbal Vocalizations**: Listeners prefer natural, understated reactions over exaggerated vocalizations. Soft sighs, sharp intakes of breath, and trembling pitch fluctuations capture deep emotional vulnerability without breaking immersion. In intimate audio, what is _not_ said often carries as much weight as the dialogue itself.

### 4. Sensory Imagery

The setting description (`THE SCENE` block) should focus on physical closeness, soft textures, temperature, skin contact, and breathing rather than dry action. A vivid sensory setting (e.g., "A quiet, candlelit bedroom. The characters are lying closely together.") subtly influences the model's baseline volume and reverberation.

### 5. What Works vs. What Doesn't

**❌ Anti-Patterns (immersion breakers):**

- **Melodramatic / Theatrical Tones**: Forcing the voice into high-pitched excitement or theatrical sadness instantly breaks immersion and sounds cartoonish.
- **Over-Narration of Physical Action**: Translating written erotica directly to audio fails when there is too much mechanical "he did this, then he did that." It feels clinical.
- **Clinical or Ultra-Crude Language**: Using rigid anatomical terms feels clinical, while overusing extreme slang breaks the fantasy. Find the natural middle ground.
- **Continuous Talking / No Dead Air**: If a character is supposedly experiencing intense emotion, talking constantly destroys the realism. The voice must have room to breathe.

**✅ What Works (the "magic"):**

- **Proximity and Intimacy Over Volume**: The listener should feel like the voice is directly inside their ear. Volume should remain low; energy should be channeled through breath.
- **The Power of the Pause**: Inserting deliberate `[medium pause]` and `[long pause]` tags between words—not just sentences—creates the illusion of a speaker who is physically overwhelmed.
- **Atmospheric Action Beats Over Dialogue Tags**: Instead of writing `"I love you," he whispered nervously`, convey the emotional state through the `THE SCENE` and `Style` notes, and let the model infer the nervous whisper naturally from context.

---

## Gay Male (M4M) Erotic Audio Guidelines

Writing and directing M4M audio requires authentic character dynamics, vocal mapping, and the elimination of traditional literary dialogue tags.

### 1. Voice Mapping Matrix

Select voices that naturally support warm, deep, and conversational ranges. Avoid high-pitched or overly energetic voices (like `Puck` or `Zephyr`) for intimate scenes, as they can sound cartoonish. Note that `Enceladus` is considered the **gold standard** for intimate audio due to its inherent breathiness and soft, velvety texture.

| Character Archetype            | Recommended Gemini Voices     | Target Acoustic Quality                    | Style & Pace Directives                                                                                                 |
| :----------------------------- | :---------------------------- | :----------------------------------------- | :---------------------------------------------------------------------------------------------------------------------- |
| **Rugged / Dominant Lead**     | `Algenib`, `Orus`, `Alnilam`  | Deep, gravelly, low-end resonance.         | Intimate, protective, quiet strength. Low projection. Measured, deliberate pacing with `[long pause]` to build tension. |
| **Vulnerable / Soft Partner**  | `Enceladus`, `Achernar`       | Soft, breathy, gentle, high glottal flow.  | Yielding, emotional, close proximity. Slightly nervous, breaking up words with `[short pause]`.                         |
| **Energetic / Playful Jock**   | `Puck`, `Fenrir`, `Sadachbia` | Upbeat, excitable, conversational, bright. | Teasing, boyish, casual, utilizing "vocal smile." Slightly faster, fluid delivery. Best for non-intimate scenes.        |
| **Warm / Comforting Roommate** | `Zubenelgenubi`, `Algieba`    | Warm, casual, relaxed, smooth.             | Soothing, friendly, supportive. Natural, slow, rhythmic breathing cadence. Ideal for aftercare scenes.                  |
| **Objective Narrator**         | `Charon`, `Iapetus`           | Clean, flat, clear cadence.                | Even, calm, non-dramatic. Professional, maintaining emotional distance.                                                 |

### 2. Avoiding Tropes & Stereotypes

- **Diverse Masculinity**: Do not map traditional masculine/feminine roles onto gay male characters. Avoid making one character very feminine/emotional and the other very masculine. Allow both characters to show strength, vulnerability, and versatile emotional states.
- **Avoid the "Female Pen" Fetishization Trap**: A common critique of M/M romance written by cis-women is that it over-writes physical descriptions in a way that feels unrealistic or biologically awkward to gay men. Prioritize dialogue and interactions that mirror authentic male bonding, teasing, and natural conversation.
- **Realistic Intimacy**: Focus on mutual consent, emotional connection, and anticipation. Characters deserve a happily ever after; avoid tragic endings that reinforce outdated tropes.
- **Camp / Flamboyant Registers**: While incredibly popular for comedic or short-form content, **avoid** flamboyant or camp speech patterns during highly intimate scenes. Stripping away theatrical speech patterns during intimate moments preserves sexual tension and realism.
- **Diverse, Inclusive Representation**: Scripts should represent diverse, healthy, consensual, and positive queer experiences. Incorporate varied accents and character backgrounds to add depth and authenticity.
- **First-Person or Soft Narrator**: To maintain the private bubble, narrative exposition should be spoken by one of the characters (acting as a first-person narrator speaking directly to the listener or thinking aloud) rather than a loud, detached third-person narrator.

### 3. Staged Writing & Eliminating "Narrative Echo"

The most critical transition when converting a raw story into a TTS script is moving from _narrative writing_ to _staged writing_. A written story relies on dialogue tags and exposition; in audio, reading these narrative beats aloud destroys the illusion of real-time interaction.

- **No Dialogue Tags**: Strip all written dialogue tags (`he said`, `Jace whispered`). The emotion should be conveyed solely by inline audio tags and the text context.
  - **Extraction**: A line written as `"Jace," I said in a breathless voice` becomes `Levi: [whispers] [breathless] Jace... [short pause]`.
- **No Action Narrative Echo**: Scriptwriters often fall into the trap of "narrative echo"—where the speaker over-explains the physical actions of the silent listener to provide context. This feels entirely unnatural.
  - ❌ **Unoptimized** (narrative echo): _"Oh, you're looking down at my hands? Are you getting nervous because I'm sitting so close to you on the couch?"_
  - ✅ **Optimized** (implication through reaction): _"Hey... [short pause] why the quiet look? [chuckles] You're not nervous... are you?"_
- **Pacing for the Listener**: The script must allocate time for the listener's imagination. Use `[medium pause]` and `[long pause]` between emotionally charged moments. Let the atmosphere and tags do the heavy lifting rather than dense dialogue.
- **Spacing consecutive tags**: To prevent API parser failures, **always** separate consecutive audio tags with spaces or punctuation (e.g., use `[sighs] [whispers]` or `[sighs], [whispers]`, **never** `[sighs][whispers]`).

### 4. Curation of the Intimacy Tag Palette

Limit the LLM prompt generator to the following safe, high-fidelity paralinguistic tags during intimate scenes. These have been tested and verified to produce natural, immersive results:

- **Breath & Voice**: `[whispers]`, `[sighs]`, `[gasp]`, `[deep breath]`, `[pant]`, `[swallows]`, `[trembling]`, `[chuckles]`, `[shivering]`.
- **Pacing**: `[short pause]` (~250ms), `[medium pause]` (~500ms), `[long pause]` (~1s+), `[slow]`.
- **Emotions**: `[adoration]`, `[interest]`, `[tension]`, `[nervousness]`, `[awe]`.

> [!WARNING]
> **Forbidden during intimate scenes**: `[shouting]`, `[excited]`, `[anger]`, `[frustration]`, `[determination]`, `[loud]`, or any tag that implies high volume or theatrical projection. These instantly break the intimate atmosphere.

---

## Refined Canonical Example (M4M Intimacy)

The following represents a production-ready, split-compliant scene prompt utilizing Jace (Algenib) and Liam (Enceladus). It demonstrates the system preamble, delimiters, proximity styling, and clean tag spacing.

```markdown
# SYSTEM PREAMBLE: Synthesize speech ONLY for the transcripts under the #### TRANSCRIPT headers. Do NOT read aloud the section titles, scene descriptions, actor names, or director notes.

# AUDIO PROFILE: Jace & Liam

## "The Rainy Evening"

### THE SCENE: A quiet cabin bedroom.

It is raining heavily outside, creating a soft, rhythmic patter against the glass. The bedroom is dim, lit only by the warm glow of the fireplace. Jace and Liam are lying close together on a plush rug. The air is quiet, cozy, and dense with unspoken tension. The acoustic environment is small, deadened, and highly intimate.

### DIRECTOR'S NOTES

Style:

- Jace (Voice: Algenib): Intimate, deep, protective. Raised soft palate. Extreme microphone proximity (proximity effect). High glottal flow. Speaks in a low register, almost murmuring.
- Liam (Voice: Enceladus): Breathy, yielding, slightly nervous. Close proximity. Soft, gentle voice with high airflow.

Pace: Measured, deliberately slow ASMR pacing. Use pauses to let the tension hang.
Accent: Standard American

#### TRANSCRIPT

Jace: [sighs] [whispers] Liam... [short pause] You're shivering.

Liam: [gasp] [nervousness] I... I didn't realize it was so cold. [short pause] Or maybe... [long pause] it's not the cold.

Jace: [adoration] Come closer then... [short pause] Let me warm you up.

Liam: [sighs] [adoration] Jace... [short pause] Your hands... they're so warm against my skin.

Jace: [slow] [whispers] Always... [long pause] I've got you.
```

## Gemini Genai API Text-to-Speech Guidelines

The following is the official reference documentation for Gemini TTS API features, voices, and audio tags.

The Gemini API can transform text input into single speaker or multi-speaker audio using Gemini text-to-speech (TTS) generation capabilities. Text-to-speech (TTS) generation is _[controllable](https://ai.google.dev/gemini-api/docs/interactions/speech-generation#controllable)_ , meaning you can use natural language to structure interactions and guide the _style_ , _accent_ , _pace_ , and _tone_ of the audio.

The TTS capability differs from speech generation provided through the [Live API](https://ai.google.dev/gemini-api/docs/live), which is designed for interactive, unstructured audio, and multimodal inputs and outputs. While the Live API excels in dynamic conversational contexts, TTS through the Gemini API is tailored for scenarios that require exact text recitation with fine-grained control over style and sound, such as podcast or audiobook generation.

This guide shows you how to generate single-speaker and multi-speaker audio from text.

> [!NOTE]
> **Note:** TTS models accept text-only inputs and produce audio-only outputs. For a complete list of restrictions specific to TTS models, review the [Limitations](https://ai.google.dev/gemini-api/docs/interactions/speech-generation#limitations) section.

### Single-speaker TTS

To convert text to single-speaker audio, set the response modality to "audio", and pass a `speech_config` object with a voice name. You'll need to choose a voice name from the prebuilt [output voices](https://ai.google.dev/gemini-api/docs/interactions/speech-generation#voices). This example saves the output audio from the model in a wave file:

#### Python Single-Speaker

    ```python
    from google import genai
    import wave
    import base64

    def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)

    client = genai.Client()

    interaction = client.interactions.create(
        model="gemini-3.1-flash-tts-preview",
        input="Say cheerfully: Have a wonderful day!",
        response_modalities=["audio"],
        generation_config={
            "speech_config": [
                {"voice": "Kore"}
            ]
        }
    )

    wave_file('out.wav', base64.b64decode(interaction.output_audio.data))
    ```

You can retrieve generated audio data by using the `interaction.output_audio` property, which returns the last generated audio block. For details on convenience properties, see the [Interactions overview](https://ai.google.dev/gemini-api/docs/interactions#convenience-properties).

### Multi-speaker TTS

For multi-speaker audio, you'll need a `multi_speaker_voice_config` object with each speaker (up to 2) configured as a `speaker_voice_config`. You'll need to define each `speaker` with the same names used in the [prompt](https://ai.google.dev/gemini-api/docs/interactions/speech-generation#controllable):

#### Python Multi-Speaker

    ```python
    from google import genai
    import wave
    import base64

    def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
       with wave.open(filename, "wb") as wf:
          wf.setnchannels(channels)
          wf.setsampwidth(sample_width)
          wf.setframerate(rate)
          wf.writeframes(pcm)

    client = genai.Client()

    prompt = """TTS the following conversation between Joe and Jane:
             Joe: How's it going today Jane?
             Jane: Not too bad, how about you?"""

     interaction = client.interactions.create(
         model="gemini-3.1-flash-tts-preview",
         input=prompt,
         response_modalities=["audio"],
         generation_config={
             "speech_config": [
                 {"speaker": "Joe", "voice": "Kore"},
                 {"speaker": "Jane", "voice": "Puck"}
             ]
         }
     )

    wave_file('out.wav', base64.b64decode(interaction.output_audio.data))
    ```

### Control speech style with prompts

You can control style, tone, accent, and pace using natural language prompts for both single- and multi-speaker TTS. For example, in a single-speaker prompt, you can say:

> Say in an spooky whisper:
>
> "By the pricking of my thumbs, Something wicked this way comes"

In a multi-speaker prompt, provide the model with each speaker's name and corresponding transcript. You can also provide guidance for each speaker individually:

> Make Speaker1 sound tired and bored, and Speaker2 sound excited and happy:
>
> Speaker1: So what's on the agenda today?
>
> Speaker2: You're never going to guess!

Try using a [voice option](https://ai.google.dev/gemini-api/docs/interactions/speech-generation#voices) that corresponds to the style or emotion you want to convey, to emphasize it even more. In the previous prompt, for example, _Enceladus_ 's breathiness might emphasize "tired" and "bored", while _Puck_'s upbeat tone could complement "excited" and "happy".

### Generate a prompt to convert to audio

The TTS models only output audio, but you can use [other models](https://ai.google.dev/gemini-api/docs/models) to generate a transcript first, then pass that transcript to the TTS model to read aloud.

#### Python Generated Prompt

    ```python
    from google import genai

    client = genai.Client()

    transcript_interaction = client.interactions.create(
       model="gemini-3.5-flash",
       input="""Generate a short transcript around 100 words that reads
                like it was clipped from a podcast by excited herpetologists.
                The hosts names are Dr. Anya and Liam."""
    )
    transcript = transcript_interaction.output_text

    tts_interaction = client.interactions.create(
       model="gemini-3.1-flash-tts-preview",
       input=transcript,
       response_modalities=["audio"],
       generation_config={
          "speech_config": [
             {"speaker": "Dr. Anya", "voice": "Kore"},
             {"speaker": "Liam", "voice": "Puck"}
          ]
       }
    )
    ```

### Supported models

- [Gemini 3.1 Flash TTS Preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview)
- [Gemini 2.5 Flash Preview TTS](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-preview-tts)
- [Gemini 2.5 Pro Preview TTS](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-pro-preview-tts)

### API Technical Specifications

> [!NOTE]
> These values are sourced from the Gemini API documentation as of June 2026. Verify against the current API docs before relying on these limits in production.

| Parameter                  | Value                                           |
| :------------------------- | :---------------------------------------------- |
| **Input Token Capacity**   | 8,192 tokens                                    |
| **Output Token Capacity**  | 16,384 tokens                                   |
| **Session Context Window** | 32,000 tokens (stateful session limit)          |
| **Max Audio Duration**     | 240 seconds per unary request                   |
| **Max Speakers Per Call**  | 2 distinct voices                               |
| **Audio Output Format**    | PCM 16-bit 24kHz raw audio data (no WAV header) |
| **Supported Codecs**       | LINEAR16 (WAV), ALAW, MULAW, MP3, OGG_OPUS, PCM |

### Safety Filter Configuration

Generating sexually explicit content via the Gemini API will trigger Google's automated safety filters, leading to `PROHIBITED_CONTENT` rejections. To prevent the generation engine from blocking erotic audio scripts, developers must explicitly adjust the threshold configuration.

The Gemini API evaluates content across four adjustable harm categories. For erotic audio, set the relevant thresholds to `BLOCK_NONE`:

```python
from google.genai import types

safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
]
```

Pass these settings in the `safety_settings` parameter of `client.interactions.create()`.

> [!WARNING]
> Setting `BLOCK_NONE` does not bypass all safety protocols. The API retains a non-adjustable layer that permanently blocks core harms (e.g., child safety violations). Applications using less restrictive safety settings may be subject to manual review. Enterprise accounts with invoiced billing are recommended for production use of explicit content generation.

## Limitations

- TTS models can only receive text inputs and generate audio outputs.
- A TTS session has a [context window](https://ai.google.dev/gemini-api/docs/long-context) limit of 32k tokens.
- Review [Languages](https://ai.google.dev/gemini-api/docs/interactions/speech-generation#languages) section for language support.
- TTS does not support streaming.

The following constraints apply specifically when using the `Gemini 3.1 Flash TTS Preview` model for speech generation:

- **Voice inconsistency with prompt instructions:** To avoid mismatched tones (such as a deep male voice attempting to speak like a young girl), ensure your prompt's written tone and context align naturally with the selected speaker's profile.
- **Quality of longer outputs:** Speech quality and consistency may degrade with length. We recommend splitting transcripts into smaller chunks.
- **Occasional text token returns:** The model occasionally returns text tokens instead of audio tokens, causing `500` error. You should implement automated retry logic in your application to handle these.
- **Prompt classifier false rejections:** Vague prompts may fail to trigger the speech synthesis classifier, resulting in a rejected request (`PROHIBITED_CONTENT`) or causing the model to read your instructions aloud. Add a clear preamble instructing the model to synthesize speech, and explicitly label where the actual spoken transcript begins.

## What's next

- Gemini's [Live API](https://ai.google.dev/gemini-api/docs/live) offers interactive audio generation options, and other modalities.
- For working with audio _inputs_, visit the [Audio understanding](https://ai.google.dev/gemini-api/docs/interactions/audio) guide.
