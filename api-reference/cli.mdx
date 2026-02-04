# Rime CLI Reference

The Rime CLI is a command-line interface for interacting Rime's text-to-speech models. It supports streaming audio generation, playback, and file output.

## Installation

```bash
# Install binary
curl -L https://rime.ai/install.sh | sh
```

## Authentication

Before using the CLI, authenticate with your Rime API key:

```bash
rime login
```

This opens your browser to copy your API key from the Rime dashboard and saves it locally to `~/.rime/cli-api-token`.

![Demo of the `rime login` command](/images/cli/login-demo.gif)

## Commands

### `rime hello`

Quick demo with a time-appropriate greeting using the Astra voice.

![Demo of the `rime hello` command](/images/cli/hello-demo.gif)

```bash
rime hello
```

**Optional Flags:**

| Flag           | Short | Description                           |
| -------------- | ----- | ------------------------------------- |
| `--output`     | `-o`  | Output file path                      |
| `--save`       | `-S`  | Save with auto-generated filename     |
| `--output-dir` | `-D`  | Directory for auto-generated filename |
| `--api-url`    | —     | Custom API URL                        |

---

### `rime tts`

Synthesize text to speech.

![Demo of the `rime tts` command](/images/cli/tts-demo.gif)

```bash
rime tts "Your text here" --speaker <voice> --model-id <model>
```

**Required Flags:**

| Flag         | Short | Description                                                             |
| ------------ | ----- | ----------------------------------------------------------------------- |
| `--speaker`  | `-s`  | Voice speaker to use (e.g., `astra`, `celeste`, `orion`)                |
| `--model-id` | `-m`  | Model ID (`arcana` for realistic voices, `mistv2` for faster synthesis) |

**Optional Flags:**

| Flag           | Short | Default | Description                                                                      |
| -------------- | ----- | ------- | -------------------------------------------------------------------------------- |
| `--output`     | `-o`  | —       | Output file path. Use `-` for stdout. If omitted, plays audio directly.          |
| `--save`       | `-S`  | `false` | Save audio with auto-generated filename                                          |
| `--output-dir` | `-D`  | —       | Directory for auto-generated filename (implies `--save`)                         |
| `--play`       | `-p`  | `false` | Play audio (default if no output specified)                                      |
| `--lang`       | `-l`  | `eng`   | Language code                                                                    |
| `--format`     | `-f`  | —       | Audio format: `wav` or `mp3` (overrides model default)                           |
| `--api-url`    | —     | —       | Custom API URL (default: `$RIME_API_URL` or `https://users.rime.ai/v1/rime-tts`) |

**Examples:**

```bash
# Play audio directly
rime tts "Hello world" -s astra -m arcana

# Save to file
rime tts "Hello world" -s astra -m arcana -o output.wav

# Save with auto-generated filename
rime tts "Hello world" -s astra -m arcana --save

# Output to stdout (pipe to another program)
rime tts "Hello world" -s astra -m arcana -o - > audio.wav

# Use MP3 format with mistv2 model
rime tts "Hello world" -s peak -m mistv2 --format mp3
```

**Model-Specific Notes:**

- `arcana`: Outputs WAV by default. Most realistic conversational voices.
- `mistv2`: Requires `--format mp3`. Faster synthesis.

---

### `rime play`

Play a WAV or MP3 file with waveform visualization.

![Demo of the `rime play` command](/images/cli/play-demo.gif)

```bash
rime play <file>
```

**Example:**

```bash
rime play output.wav
```

---

### `rime curl`

Generate a curl command for making TTS API requests.

```bash
rime curl [text] [flags]
```

Run without arguments to see an example command:

```bash
rime curl
```

**Optional Flags:**

| Flag         | Short | Default  | Description                                           |
| ------------ | ----- | -------- | ----------------------------------------------------- |
| `--speaker`  | `-s`  | `astra`  | Voice speaker                                         |
| `--model-id` | `-m`  | `arcana` | Model ID                                              |
| `--lang`     | `-l`  | `eng`    | Language code                                         |
| `--show-key` | —     | `false`  | Include actual API key (default: `$RIME_CLI_API_KEY`) |
| `--oneline`  | —     | `false`  | Output as single line for easy copy-paste             |
| `--api-url`  | —     | —        | Custom API URL                                        |

**Examples:**

```bash
# Generate example curl command
rime curl

# Generate curl with your text
rime curl "Hello from Rime" -s celeste -m arcana

# Single-line output with API key
rime curl "Hello" -s astra -m arcana --oneline --show-key
```

---

### `rime login`

Authenticate with your Rime API key.

```bash
rime login
```

Opens the Rime dashboard in your browser to copy your API key, then saves it to `~/.rime/cli-api-token`.

---

### `rime uninstall`

Show removal instructions for the CLI and configuration.

```bash
rime uninstall
```

## Global Flags

These flags work with all commands:

| Flag        | Short | Description                   |
| ----------- | ----- | ----------------------------- |
| `--quiet`   | `-q`  | Suppress non-essential output |
| `--json`    | —     | Output results as JSON        |
| `--version` | —     | Print version information     |
| `--help`    | `-h`  | Help for any command          |

## Environment Variables

| Variable             | Description                                         |
| -------------------- | --------------------------------------------------- |
| `RIME_CLI_API_KEY`   | API key for authentication (overrides stored token) |
| `RIME_API_URL`       | Custom API endpoint URL                             |
| `RIME_DASHBOARD_URL` | Custom dashboard URL for login                      |

## Output Formats

### Audio Formats

| Format | Extension | Use Case                                                |
| ------ | --------- | ------------------------------------------------------- |
| WAV    | `.wav`    | Default for `arcana` model. High quality, larger files. |
| MP3    | `.mp3`    | Required for `mistv2` model. Compressed, smaller files. |

### JSON Output

When using `--json`, the CLI outputs structured data:

```json
{
  "ttfb_ms": 245,
  "duration_ms": 3200,
  "size_bytes": 76800,
  "output_file": "output.wav",
  "text": "Hello world",
  "speaker": "astra",
  "model_id": "arcana",
  "lang": "eng"
}
```

## Auto-Generated Filenames

When using `--save` or `--output-dir`, filenames follow this pattern:

```
rime-<speaker>-<model>-<lang>_<sanitized-text>.<ext>
```

Example: `rime-astra-arcana-eng_hello-world.wav`

## Metadata Embedding

Audio files saved by the CLI include embedded metadata. This way, when you run `rime play` on the file, you can still see the voice, model, and transcript. You can also see this metadata in e.g. Preview or Finder, or any media library/player.

**WAV files (LIST/INFO chunk):**

- `IART` (Artist): `Rime AI TTS`
- `INAM` (Name): Voice and model info
- `ICMT` (Comment): Full synthesis parameters and text

**MP3 files (ID3v2.3 tags):**

- `TPE1` (Artist): `Rime AI TTS`
- `TIT2` (Title): Voice and model info
- `COMM` (Comment): Full synthesis parameters and text

## Troubleshooting

### "API key not found"

Run `rime login` or set `RIME_CLI_API_KEY`:

```bash
export RIME_CLI_API_KEY=your_key_here
```

### "authentication failed: invalid API key"

Verify your API key at [app.rime.ai/tokens](https://app.rime.ai/tokens).

### "mist and mistv2 models require --format mp3"

The `mistv2` model only supports MP3 output:

```bash
rime tts "text" -s cove -m mistv2 --format mp3
```

### No audio playback

If audio doesn't play:

- Check system audio settings
- Try saving to file instead: `rime tts "text" -s astra -m arcana -o output.wav`
