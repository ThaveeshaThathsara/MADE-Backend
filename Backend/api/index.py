from main import app

# This is the entry point for Vercel
handler = app
```

### Step 4: Update GitHub

Push these changes to GitHub:
```
Backend/
├── api/
│   └── index.py  ← NEW FILE
├── main.py
├── vercel.json   ← UPDATED
└── requirements.txt
