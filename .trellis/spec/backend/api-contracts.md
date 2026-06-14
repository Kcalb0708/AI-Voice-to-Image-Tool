# Backend API Contracts

## Scenario: Voice Drawing Provider Proxy

### 1. Scope / Trigger

- Trigger: the voice drawing MVP defines new backend APIs, provider environment keys, and a cross-layer drawing command contract consumed by the Vue frontend.
- Applies to: FastAPI routes under `backend/app/routers/`, provider clients under `backend/app/services/`, and Pydantic models in `backend/app/models.py`.

### 2. Signatures

- `GET /api/health -> {"status": "ok"}`
- `POST /api/asr` with multipart field `audio: UploadFile -> {"text": string}`
- `POST /api/interpret` with JSON `{"text": string, "elements": DrawingElement[]} -> InterpretResponse`

Core models:

```python
class DrawingElement(BaseModel):
    id: str
    tag: str
    attrs: dict[str, Any]
    text: str | None = None

class DrawingCommand(BaseModel):
    action: Literal["add", "modify", "delete", "clear", "export"]
    id: str | None = None
    tag: str | None = None
    attrs: dict[str, Any] = {}
    text: str | None = None
```

### 3. Contracts

Request contracts:

- `/api/asr` requires a non-empty uploaded audio file.
- The browser recorder should use native `MediaRecorder` capture, decode the recorded blob in-browser, and upload mono 16-bit WAV (`audio/wav`, filename `speech.wav`) for provider compatibility.
- The browser recorder should reject only recordings with no captured audio data or very short duration; do not hard-block low-volume recordings before ASR because local amplitude checks can produce false positives.
- Browser audio uploads may include codec parameters such as `audio/webm;codecs=opus`; strip MIME parameters before forwarding the multipart file to the ASR provider.
- `/api/interpret.text` is required and is capped at 2000 characters.
- `/api/interpret.elements` is an optional list capped at 200 current elements.

Response contracts:

- ASR returns only `{text}` to the browser.
- Interpret returns `{commands, reply, warnings}`.
- Invalid individual commands are skipped and reported in `warnings`; the whole request should still succeed when at least the provider response is parseable.
- User-facing `detail`, `warnings`, and LLM `reply` strings must be Simplified Chinese.
- LangChain system prompts must explicitly require Chinese `reply` output.

Environment contracts:

- `ASR_API_URL`, `ASR_API_KEY`, `ASR_MODEL`, `ASR_LANGUAGE`, `ASR_RESPONSE_FORMAT`, `ASR_TIMEOUT_SECONDS`
- `ASR_API_URL` may be either a base URL or a full `/audio/transcriptions` endpoint; normalize base URLs before posting audio.
- `ASR_MODEL` defaults to `gpt-4o-mini-transcribe`.
- `ASR_LANGUAGE` defaults to `zh`; `ASR_RESPONSE_FORMAT` defaults to `json`.
- `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_STRUCTURED_OUTPUT_METHOD`
- `LLM_API_URL` is accepted only as legacy compatibility; if it ends with `/chat/completions`, normalize it to the base URL required by LangChain `init_chat_model`.

### 4. Validation & Error Matrix

- Empty audio upload -> `400`
- Missing ASR configuration -> `503`
- ASR provider/network/unreadable response -> `502`
- ASR provider non-2xx response -> `502` with the provider status code and a sanitized provider error message when available
- ASR provider returns success without recognized text -> `502` with a Chinese message that asks the user to confirm clear speech was recorded
- Missing LLM configuration -> `503`
- LLM provider/network/unreadable structured output -> `502`
- LLM output fails Pydantic schema validation -> `502`
- Unsupported SVG tag/attribute in one command -> skip command and include warning
- Provider/configuration failures surfaced to the frontend -> Chinese `detail`

### 5. Good/Base/Bad Cases

- Good: a valid transcript plus current element summary returns one or more sanitized commands and a short reply.
- Good: browser recording uploads `speech.wav` with `audio/wav`, and the ASR provider returns `{text}`.
- Base: a valid provider response includes one unsafe command and one safe command; the unsafe command is skipped and the safe command is returned.
- Bad: browser recording contains only silence; backend should return a clear Chinese error if the ASR provider accepts the file but returns no text.
- Bad: browser recording is captured by a hand-written `ScriptProcessorNode` PCM pipeline that can produce valid-but-silent WAV files in some browsers; prefer native `MediaRecorder` capture followed by in-browser WAV transcoding.
- Bad: browser recording uploads WebM/Opus to an OpenAI-compatible gateway that rejects or 500s on that container; prefer WAV encoding before upload.
- Bad: provider returns malformed JSON or a schema-incompatible command object; return `502` instead of forwarding unsafe data.
- Bad: backend returns English error details such as `"Command interpretation failed"`; return a Chinese message instead.

### 6. Tests Required

- `svg_sanitizer` accepts allowed SVG tags/attrs and rejects scripts/events/external references.
- `/api/interpret` returns sanitized commands when the LLM client returns a valid payload.
- `/api/interpret` skips unsafe single commands while preserving valid commands.
- Config tests assert missing provider keys fail explicitly and legacy `LLM_API_URL` normalization works.
- ASR client tests assert upload MIME parameters are stripped and provider error messages are sanitized before being surfaced.
- Frontend recorder tests assert WAV blobs contain a valid RIFF/WAVE header, mono PCM format, sample rate, and data length.
- UI-facing error/message scans should check common English strings after localization work.

### 7. Wrong vs Correct

#### Wrong

```python
# Do not pass provider JSON directly to the frontend.
return provider_payload
```

#### Correct

```python
interpreted = InterpretResponse.model_validate(provider_payload)
commands, warnings = sanitize_commands(interpreted.commands, request.elements)
return InterpretResponse(commands=commands, reply=interpreted.reply, warnings=warnings)
```
