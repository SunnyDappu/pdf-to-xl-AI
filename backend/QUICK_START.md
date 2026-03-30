# 🚀 Quick Start - API Key & Running the App

## Step 1: Get Your Claude API Key

1. Go to: **https://console.anthropic.com/api_keys**
2. Sign up / Log in to your Anthropic account
3. Click **Create Key**
4. Copy the key (starts with `sk-ant-`)
5. **IMPORTANT**: Save it immediately - you can't see it again!

## Step 2: Add API Key to .env

Open `backend\.env` and replace:
```env
ANTHROPIC_API_KEY=sk-ant-v0-xxxxxxxxxxxxxxxx
```

With your actual key:
```env
ANTHROPIC_API_KEY=sk-ant-v0-abc123xyz...
```

**Save the file!**

## Step 3: Start the Application

From `backend` directory:

```powershell
# Make sure venv is set up
$env:PATH = ".\venv\Scripts;" + $env:PATH

# Run the app
.\venv\Scripts\python.exe app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

## Step 4: Open in Browser

Visit: **http://localhost:5000**

You should see the beautiful PDF-to-Excel upload interface! 🎉

---

## ✅ Verification Checklist

- ✅ Tesseract installed: `v5.5.0`
- ✅ Python dependencies: All installed
- ✅ .env file: Created
- ✅ API Key: Ready to add

---

## 🎯 Test the App

1. **Upload a PDF** - Drag/drop or click to select
2. **Enter Request** - Example: "Extract all names and emails"
3. **Click Start** - Watch the progress
4. **Download Excel** - Get your results

---

## ⏱️ Expected Time

- **Setup**: ~2 hours (first time, including installations)
- **Running**: ~1 minute startup
- **Processing**: 2-30 minutes (depends on PDF size)

---

## 🐛 Quick Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 5000 in use | Change PORT in .env or `netstat -ano \| findstr :5000` |
| API Key error | Add key to .env and restart |
| Module not found | Run: `.\venv\Scripts\python.exe app.py` (use full path) |

---

## 📞 Need Help?

Check **SETUP.md** for detailed troubleshooting!
