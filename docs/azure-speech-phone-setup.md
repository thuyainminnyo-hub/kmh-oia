# KMH Azure Speech Adapter — Phone-first setup

## Create the Azure resource
1. On a phone browser, sign in at https://portal.azure.com.
2. Create a **Speech** resource (not just an Azure account). Review pricing and quotas before creation.
3. Open the resource's **Keys and Endpoint** page. Keep the key private and note the resource region identifier.
4. Confirm the selected region supports the required Speech features and the Burmese locale/voice.

## Configure secrets (never commit them)
Set these environment variables on the server or deployment environment:
- `SPEECH_KEY`: the Speech resource key
- `SPEECH_REGION`: region identifier, for example the region actually shown on the resource

Do not paste secrets into chat, source code, screenshots, issue comments, or test fixtures. For hosted CI, use repository Settings → Secrets and variables → Actions → New repository secret. A GitHub Actions secret does not automatically become available to a workflow; the workflow must explicitly map it to environment variables, and a real-provider test should be opt-in to avoid surprise charges.

## Adapter contract and limitations
- `src/azure_speech_adapter.py` implements provider-neutral `transcribe(AudioInput)` and `synthesize(text)`.
- STT currently accepts structurally valid WAV files only and uses Azure's short-audio REST endpoint.
- TTS returns MP3 bytes (`audio/mpeg`); it does not play audio or capture a microphone.
- Unit tests use a fake HTTP function. They do not call Azure, verify credentials, incur charges, or measure real Burmese quality.
- The existing `VoiceRuntime` expects its own `AudioFrame` interface; a small bridge/integration layer is still needed before this adapter can replace the deterministic codec end-to-end.
- Do not log raw audio or provider keys. Use consented audio samples and human-checked reference transcripts for accuracy evaluation.

## Official guides
- Speech-to-text: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-speech-to-text?pivots=programming-language-python
- Speech regions: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions?tabs=llmspeech
- Text-to-speech REST API: https://learn.microsoft.com/azure/ai-services/speech-service/rest-text-to-speech
