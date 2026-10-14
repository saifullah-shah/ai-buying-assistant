## M6 LLM API Integration Research Log

### Date: 2026-10-13

### Objective
Install and configure the Google Generative AI SDK (`google-generativeai`) for M6 LLM integration using the Gemini API key in `.env`. Test the API call with M4 prompt format.

### Steps Taken

1. **Initial SDK install attempt** (`pip install google-generativeai`):
   - Failed with `OSError: [WinError 2] The system cannot find the file specified: 'C:\python312\Scripts\tqdm.exe'`
   - Also failed with `idna.exe` and `cffi-gen-src.exe` missing
   - Python 3.12 installation had missing executable files needed by pip

2. **Resolved dependency chain**:
   Installed packages individually using `pip install --break-system-packages --no-deps`:
   - `google-generativeai-0.8.6` (main SDK)
   - `google-ai-generativelanguage-0.12.1` (required dependency)
   - `google-api-core-2.42.0` (required dependency)
   - `google.auth-2.62.0` (required dependency)
   - `cryptography-50.0.2` (required dependency)
   - `pydantic-2.14.1` (required dependency)
   - `googleapiclient` (via `google-api-python-client-2.201.0`)

3. **SDK verification**:
   - `import google.generativeai as genai` ✅ works
   - `genai.configure(api_key=api_key)` ✅ works
   - `genai.GenerativeModel('gemini-pro')` ✅ constructor succeeds
   - `model.generate_content(prompt)` ⚠️ 404 Not Found (model not available for this API key/Project)

4. **M4 prompt format testing**:
   - Constructed M4 prompt with FITS BECAUSE/WHAT IT SACRIFICES/UNKNOWN AND WHY/CONSTRAINT COMPLIANCE SUMMARY sections
   - SDK accepts the prompt format
   - API response depends on model availability

5. **Project state updates**:
   - Updated `docs/PROJECT_STATE.md` with M6 status
   - Verified `docs/DECISIONS.md` has D-011 recorded

### Key Findings

| Issue | Resolution |
|---|---|
| `pip install google-generativeai` fails due to missing `tqdm.exe`, `idna.exe`, `cffi-gen-src.exe` | Installed dependencies individually with `--no-deps` flag |
| `google.generativeai` import fails due to missing `google.ai`, `google.api_core`, `google.auth`, `cryptography`, `pydantic` | Installed each dependency with `--no-deps` |
| Model `gemini-pro` returns 404 Not Found | Model not available for this API key/Project; needs selection |
| `google.generativeai` deprecated in favor of `google.genai` | SDK still works for now; FutureWarning issued |

### Files Modified

- `docs/PROJECT_STATE.md`: Updated M6 status section
- `docs/DECISIONS.md`: D-011 (LLM API Integration) recorded

### Next Steps

1. Select correct model name for Gemini API key/Project
2. Update `.env` `GEMINI_MODEL` with compatible model ID
3. Test `model.generate_content()` with M4 prompt format
4. Implement response parsing (FITS BECAUSE/WHAT IT SACRIFICES/UNKNOWN AND WHY/CONSTRAINT COMPLIANCE SUMMARY)
5. Validate grounding using M4 evidence citation functions

### SDK Installation Commands (for reference)

```bash
# Install google-generativeai SDK (bypassing missing executable issue)
pip install google-generativeai --no-deps --break-system-packages

# Install required dependency chain
pip install google-ai-generativelanguage --no-deps --break-system-packages
pip install google-api-core --no-deps --break-system-packages
pip install google.auth --no-deps --break-system-packages
pip install cryptography --no-deps --break-system-packages
pip install pydantic --no-deps --break-system-packages
```