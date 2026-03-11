# Omniscient Life OS Agent: Start, Stop, and Interact

This guide shows exactly how to run the agent on Windows, how to stop it safely, and how to interact with it effectively.

## 1. Start Running the Agent

### Step 1: Open terminal in the project folder
Open a terminal and navigate to your project folder:
```powershell
cd "path\to\Omniscient Life OS"
```

### Step 2: Activate virtual environment (recommended)
```powershell
.venv\Scripts\activate
```

If you do not have a venv yet:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Ensure API key is configured
Your `.env` file should contain:
```env
GEMINI_API_KEY=your_api_key_here
```

### Step 4: Run the agent
```powershell
python main.py
```

### Step 5: Confirm it is running
You should see logs similar to:
```text
Connecting to Gemini Live with model: models/gemini-2.5-flash-native-audio-latest
Initializing audio and sensor streams...
Connected to Gemini Live!
Agent is now listening and watching. Speak to interact.
```

## 2. How to Stop the Agent

### Normal stop (best method)
In the same terminal where it is running:
```text
Ctrl + C
```

### If it does not stop
Find running `main.py` processes:
```powershell
Get-CimInstance Win32_Process |
Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'main.py' } |
Select-Object ProcessId, CommandLine
```

Stop them:
```powershell
Get-CimInstance Win32_Process |
Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'main.py' } |
ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

### Emergency stop (kills all Python processes)
Use only if needed:
```powershell
taskkill /IM python.exe /F
```

## 3. How to Interact with the Agent

The agent supports multimodal interaction:

1. Voice input: speak naturally into your microphone.
2. Visual context: it observes webcam and screen frames in the background.
3. Tool use: it can run terminal commands and access memory tools when needed.

### Interaction examples
Say things like:

1. "Summarize what is on my screen right now."
2. "Remember that my target bedtime is 11:00 PM."
3. "Search my memory for anything about diet goals."
4. "Help me debug this Python error and run the fix in terminal."

### Best practices for good responses

1. Speak clearly and pause briefly between requests.
2. Ask one task at a time for better tool execution.
3. Be explicit when you want actions: "run this command", "save this memory", "search memory for X".

## 4. Quick Command Cheat Sheet

Start:
```powershell
cd "path\to\Omniscient Life OS"
.venv\Scripts\activate
python main.py
```

Stop (normal):
```text
Ctrl + C
```

Stop (force only `main.py`):
```powershell
Get-CimInstance Win32_Process |
Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'main.py' } |
ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

## 5. Common Issues

1. `NOT_FOUND` model error:
	- Ensure `main.py` uses `models/gemini-2.5-flash-native-audio-latest`.
2. No response but no error:
	- Wait a few seconds at startup for model loading.
3. Mic/camera not working:
	- Check Windows privacy permissions for microphone and camera.
4. API key errors:
	- Verify `.env` has a valid `GEMINI_API_KEY`.


