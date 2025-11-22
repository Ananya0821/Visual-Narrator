import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STORE = {}  # id -> caption

HF_TOKEN = os.getenv("HF_TOKEN")  # optional
OPENAI_KEY = os.getenv("OPENAI_API_KEY")  # optional


def caption_image_bytes(img_bytes: bytes):
    # fallback if no HuggingFace key
    if not HF_TOKEN:
        return "A placeholder caption (add HF_TOKEN for real captions)."

    url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    try:
        resp = requests.post(url, headers=headers, data=img_bytes, timeout=30)
        resp.raise_for_status()
        r = resp.json()
        if isinstance(r, list):
            return r[0].get("generated_text", "An interesting image.")
        return r.get("generated_text", "An interesting image.")
    except Exception:
        return "An interesting image."


def weave_story(captions, tone="playful"):
    # If no OpenAI key, return a simple combined string
    if not OPENAI_KEY:
        return " ".join(captions) if captions else "No images yet. Upload some photos to create a story!"
    prompt = (
        "You are a creative storyteller. Connect these image captions into a single short story.\n\n"
        + "\n".join([f"{i+1}. {c}" for i, c in enumerate(captions)])
        + f"\n\nWrite a coherent, engaging short story (3-6 short paragraphs) in a {tone} tone. Keep names consistent and end with a satisfying conclusion."
    )
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 600,
        "temperature": 0.8,
    }
    try:
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        out = resp.json()
        return out["choices"][0]["message"]["content"].strip()
    except Exception:
        return " ".join(captions) if captions else "No images yet. Upload some photos to create a story!"

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    content = await file.read()
    caption = caption_image_bytes(content)
    img_id = str(uuid.uuid4())
    STORE[img_id] = caption
    return {"id": img_id, "caption": caption, "filename": file.filename}

@app.post("/story")
async def get_story(data: dict):
    ids = data.get("ordered_ids", [])
    captions = [STORE.get(i, "an image of something mysterious") for i in ids]
    story = weave_story(captions, tone=data.get("tone", "playful"))
    return {"story": story, "captions": captions}
