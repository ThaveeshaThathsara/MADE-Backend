FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

5. Click **"Commit changes"**

### Then in Koyeb:

1. **Builder:** Choose **"Docker"**
2. **Dockerfile:** `Dockerfile`
3. **Port:** `8000`
4. Add environment variable: `MONGODB_URI`
5. Click **"Deploy"**

---

## 📊 Your Backend Folder Should Have:
```
Backend/
├── main.py ✅
├── requirements.txt ✅
├── Procfile ✅
├── Dockerfile ← ADD THIS!
├── api/
│   └── index.py
└── memory/
