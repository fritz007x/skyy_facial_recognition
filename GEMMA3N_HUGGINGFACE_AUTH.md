# Hugging Face Authentication Guide for Gemma 3n Models

This guide explains how to set up Hugging Face authentication to access the gated Gemma 3n models.

## What is a "Gated Model"?

Gemma 3n models are **gated models** on Hugging Face, meaning:
- They require user authentication to download
- You must explicitly request access to the model
- You need a Hugging Face account and API token
- This is Google's way of controlling access and tracking usage of their models

## Why is Authentication Required?

The error you're seeing:
```
GatedRepoError: 401 Client Error
Cannot access gated repo for url https://huggingface.co/google/gemma-3n-E2B-it/resolve/main/config.json.
Access to model google/gemma-3n-E2B-it is restricted. You must have access to it and be authenticated to access it.
```

This means:
1. The Gemma 3n model repository requires authentication
2. You haven't logged in with Hugging Face credentials
3. OR you haven't requested access to the specific model

## Step-by-Step Setup

### Step 1: Create a Hugging Face Account

1. Go to [huggingface.co](https://huggingface.co)
2. Click "Sign Up" in the top right
3. Create your free account with email/password or social login
4. Verify your email address

### Step 2: Request Access to Gemma 3n Models

You need to request access for EACH model variant you want to use:

**For Gemma 3n E2B (2 billion parameters):**
1. Visit: [https://huggingface.co/google/gemma-3n-E2B-it](https://huggingface.co/google/gemma-3n-E2B-it)
2. Click the "Request Access" button
3. Review and accept Google's terms of use
4. Wait for approval (usually instant or within a few minutes)

**For Gemma 3n E4B (4 billion parameters):**
1. Visit: [https://huggingface.co/google/gemma-3n-E4B-it](https://huggingface.co/google/gemma-3n-E4B-it)
2. Click the "Request Access" button
3. Accept the terms
4. Wait for approval

**Note:** You must request access separately for each model variant. Access to E2B does NOT grant access to E4B.

### Step 3: Get Your Hugging Face API Token

1. Log in to [huggingface.co](https://huggingface.co)
2. Click your profile picture (top right) → **Settings**
3. In the left sidebar, click **Access Tokens**
4. Click **New token**
5. Configure your token:
   - **Name**: Give it a descriptive name (e.g., "gemma3n-local-dev")
   - **Type**: Choose "Read" (sufficient for downloading models)
   - **Scope**: Leave default or select specific repositories if needed
6. Click **Generate token**
7. **IMPORTANT**: Copy the token immediately - you won't be able to see it again!
   - It looks like: `hf_aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890`

### Step 4: Authenticate with Hugging Face

You have **two options** for authentication:

#### Option A: Use Environment Variable (Recommended for Development)

This is the simplest method for local development:

**Windows (Command Prompt):**
```cmd
set HF_TOKEN=hf_your_token_here
python src\gemma3n_native_audio_assistant.py test_audio\hello_gemma.wav
```

**Windows (PowerShell):**
```powershell
$env:HF_TOKEN = "hf_your_token_here"
python src\gemma3n_native_audio_assistant.py test_audio\hello_gemma.wav
```

**Linux/Mac:**
```bash
export HF_TOKEN=hf_your_token_here
python src/gemma3n_native_audio_assistant.py test_audio/hello_gemma.wav
```

**Make it Permanent:**

To avoid setting the token every time:

- **Windows**: Add to System Environment Variables
  1. Search "Environment Variables" in Windows Start
  2. Click "Environment Variables" button
  3. Under "User variables", click "New"
  4. Variable name: `HF_TOKEN`
  5. Variable value: Your token (e.g., `hf_aBcDeFg...`)
  6. Click OK
  7. Restart your terminal

- **Linux/Mac**: Add to `~/.bashrc` or `~/.zshrc`
  ```bash
  echo 'export HF_TOKEN=hf_your_token_here' >> ~/.bashrc
  source ~/.bashrc
  ```

#### Option B: Use Hugging Face CLI (Recommended for Production)

This method stores your token securely in `~/.huggingface/token`:

1. **Install the Hugging Face CLI** (if not already installed):
   ```bash
   pip install huggingface-hub
   ```

2. **Login using the CLI**:
   ```bash
   huggingface-cli login
   ```

3. **Enter your token when prompted**:
   ```
   _|    _|  _|    _|    _|_|_|    _|_|_|  _|_|_|  _|      _|    _|_|_|      _|_|_|_|    _|_|      _|_|_|  _|_|_|_|
   _|    _|  _|    _|  _|        _|          _|    _|_|    _|  _|            _|        _|    _|  _|        _|
   _|_|_|_|  _|    _|  _|  _|_|  _|  _|_|    _|    _|  _|  _|  _|  _|_|      _|_|_|    _|_|_|_|  _|        _|_|_|
   _|    _|  _|    _|  _|    _|  _|    _|    _|    _|    _|_|  _|    _|      _|        _|    _|  _|        _|
   _|    _|    _|_|      _|_|_|    _|_|_|  _|_|_|  _|      _|    _|_|_|      _|        _|    _|    _|_|_|  _|_|_|_|

   To login, `huggingface_hub` requires a token generated from https://huggingface.co/settings/tokens .
   Token:
   ```

4. **Paste your token and press Enter**

5. **Verify authentication**:
   ```bash
   huggingface-cli whoami
   ```

   You should see:
   ```
   your-username
   ```

### Step 5: Verify Authentication Works

Run this simple test to verify everything is set up correctly:

```python
from huggingface_hub import login, whoami

# Try to get current user
try:
    user_info = whoami()
    print(f"Authenticated as: {user_info['name']}")
    print("Authentication successful!")
except Exception as e:
    print(f"Not authenticated: {e}")
    print("Please login with: huggingface-cli login")
```

Or from the command line:
```bash
python -c "from huggingface_hub import whoami; print('Authenticated as:', whoami()['name'])"
```

## Troubleshooting

### Error: "401 Client Error" or "Access Denied"

**Possible causes:**
1. You haven't requested access to the model
2. Your access request is still pending
3. You're not authenticated
4. Your token has expired or is invalid

**Solutions:**
1. Check that you've requested access at the model's Hugging Face page
2. Verify you're logged in: `huggingface-cli whoami`
3. Re-login: `huggingface-cli login`
4. Generate a new token if the old one expired

### Error: "Token is invalid"

Your token may have been deleted or expired.

**Solution:**
1. Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Delete the old token
3. Create a new token
4. Re-authenticate with `huggingface-cli login`

### Error: "No such file or directory: ~/.huggingface/token"

You haven't logged in yet.

**Solution:**
```bash
huggingface-cli login
```

### Environment Variable Not Working

Make sure:
- The variable name is exactly `HF_TOKEN` (case-sensitive on Linux/Mac)
- You've restarted your terminal after setting it
- You're using the correct syntax for your shell (cmd vs PowerShell vs bash)

### Access Request Still Pending

Usually, access is granted instantly, but sometimes it may take a few minutes.

**What to do:**
1. Check your email for approval notification
2. Visit the model page and check if "Request Access" changed to "Access Granted"
3. Try refreshing the page
4. If it takes more than 24 hours, check Hugging Face's status page or forums

## Security Best Practices

### DO:
- Keep your token secret (treat it like a password)
- Use read-only tokens for downloading models
- Store tokens in environment variables or secure credential managers
- Regenerate tokens periodically

### DON'T:
- Commit tokens to Git repositories
- Share tokens publicly
- Use write tokens when read access is sufficient
- Store tokens in plain text files in your project

## Token Storage Locations

When you authenticate, your token is stored in:

- **huggingface-cli login**: `~/.huggingface/token`
  - Windows: `C:\Users\YourName\.huggingface\token`
  - Linux/Mac: `~/.huggingface/token`

- **Environment variable**: Stored in system/shell configuration
  - Windows: System Environment Variables
  - Linux/Mac: `~/.bashrc`, `~/.zshrc`, etc.

## Using the Token in Code

The updated `gemma3n_native_audio_assistant.py` will automatically use your token in this order:

1. Environment variable `HF_TOKEN`
2. Stored token from `huggingface-cli login` (in `~/.huggingface/token`)

You don't need to modify the code - just authenticate once and it will work!

## Quick Reference

| Method | Command | Token Location |
|--------|---------|----------------|
| Environment Variable | `set HF_TOKEN=hf_...` (Windows)<br>`export HF_TOKEN=hf_...` (Linux/Mac) | Current session or system env vars |
| CLI Login | `huggingface-cli login` | `~/.huggingface/token` |
| Check Auth | `huggingface-cli whoami` | - |

## Next Steps

After authentication is set up:

1. **Install all dependencies** (including timm - CRITICAL):
   ```bash
   pip install transformers>=4.53.0 torch torchaudio timm>=0.9.0 huggingface-hub pyttsx3
   ```

   **Important:** The `timm` (PyTorch Image Models) library is REQUIRED for Gemma 3n:
   - Gemma 3n is a unified multimodal model (audio + vision + text)
   - Even for audio-only use, the model architecture requires vision components
   - Without `timm`, you'll get: `TimmWrapperModel requires the timm library`

2. Run the Gemma 3n assistant:
   ```bash
   python src\gemma3n_native_audio_assistant.py test_audio\hello_gemma.wav
   ```

3. The model will download automatically on first run (~2-4 GB for E2B)

4. Subsequent runs will use the cached model (much faster!)

## Additional Resources

- [Hugging Face Documentation - Security](https://huggingface.co/docs/hub/security-tokens)
- [Hugging Face Hub Python Library](https://huggingface.co/docs/huggingface_hub)
- [Gemma Model Card](https://huggingface.co/google/gemma-3n-E2B-it)

---

**Need Help?**

If you're still having issues after following this guide:
1. Check the [Hugging Face Status Page](https://status.huggingface.co/)
2. Visit the [Hugging Face Forums](https://discuss.huggingface.co/)
3. Check the project's issue tracker
