import os
import json
import re
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from pdfminer.high_level import extract_text
import docx
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
collection_name = "biro_baza"

# Brisemo i ponovo kreiramo kolekciju sa optimalnim parametrima
if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

def chunk_text(text, chunk_size=200, overlap=40):
    text = re.sub(r'\n+', '\n', text)
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def procitaj_fajl(putanja):
    ext = putanja.suffix.lower()
    if ext == ".pdf":
        return extract_text(putanja)
    elif ext == ".docx":
        doc = docx.Document(putanja)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    elif ext in [".txt", ".csv", ".json"]:
        with open(putanja, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return ""

def upload_data():
    point_id = 1
    
    # 1. Uvoz zaposlenih iz JSON-a
    json_path = Path(r"D:\Birogemini\zaposleni_baza.json")
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            zaposleni = json.load(f)
            for z in zaposleni:
                text = f"Zaposleni: {z['ime_prezime']}, Funkcija: {z['funkcija']}, Opis: {z['opis']}"
                vector = model.encode(text).tolist()
                client.upsert(
                    collection_name=collection_name,
                    points=[PointStruct(id=point_id, vector=vector, payload={"type": "zaposleni", **z})]
                )
                point_id += 1
        print(f"✅ Ubačeno {len(zaposleni)} zaposlenih u Qdrant.")

    # 2. Folderi za skeniranje
    target_folderi = [
        Path(r"D:\Dokumenti"),
        Path(r"D:\Birogemini\ekstrahovane_slike")
    ]

    for osnovni_folder in target_folderi:
        if not osnovni_folder.exists():
            continue

        print(f"\n⏳ Skeniram: {osnovni_folder}...")
        for putanja in osnovni_folder.rglob("*"):
            if putanja.is_dir() or putanja.name.startswith("~$") or putanja.name.endswith(".tmp"):
                continue

            tekst = procitaj_fajl(putanja)
            if not tekst.strip() and putanja.suffix.lower() in [".jpg", ".png", ".jpeg", ".bmp"]:
                tekst = f"Dijagram / Slika iz osnove: {putanja.stem} u folderu {putanja.parent.name}"
            
            if not tekst.strip():
                continue

            print(f"📄 Indeksiram: {putanja.name}")
            chunks = chunk_text(tekst, chunk_size=200, overlap=40)
            for chunk in chunks:
                vector = model.encode(chunk).tolist()
                client.upsert(
                    collection_name=collection_name,
                    points=[PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "type": "dokument",
                            "naziv_fajla": putanja.name,
                            "folder": putanja.parent.name,
                            "sadrzaj": chunk,
                            "putanja": str(putanja)
                        }
                    )]
                )
                point_id += 1

    print("\n🎉 Re-indeksiranje kompletirano sa optimalnim chunk-ovima!")

if __name__ == "__main__":
    upload_data()