import streamlit as st
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from groq import Groq
import os
import re
import json
import urllib.request
import urllib.parse
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import unicodedata
import base64
import time

# --- LANGGRAPH ---
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Any

load_dotenv()

st.set_page_config(page_title="Biro AI Asistent", layout="wide")

# Cloudflare R2 Public Access URL-ovi
R2_BASE_URL = "https://pub-49fb3cc788a74e0a9edbac7e11305b94.r2.dev"
LOGO_BIRO_URL = f"{R2_BASE_URL}/biro_logo.jpg"
LOGO_SRBIJASUME_URL = f"{R2_BASE_URL}/srbijasume_logo.jpg"

@st.cache_resource
def get_clients():
    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    groq = Groq()
    return client, model, groq

qdrant_client, encoder, groq_client = get_clients()

@st.cache_resource
def ucitaj_podatke_iz_baze():
    svi_zaposleni = []
    svi_dokumenti = []
    try:
        offset = None
        while True:
            res, offset = qdrant_client.scroll(
                collection_name="biro_baza",
                limit=250,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            for pt in res:
                p = pt.payload or {}
                if p.get("type") == "zaposleni":
                    svi_zaposleni.append(p)
                else:
                    svi_dokumenti.append(pt)
            if offset is None:
                break
    except Exception:
        pass
    return svi_zaposleni, svi_dokumenti

def normalize_str(s):
    if not s:
        return ""
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower().strip()

def cir_to_lat(text):
    if not text:
        return ""
    mapping = {
        'љ': 'lj', 'њ': 'nj', 'џ': 'dž',
        'Љ': 'Lj', 'Њ': 'Nj', 'Џ': 'Dž',
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'ђ': 'đ', 'е': 'e', 'ж': 'ž', 'з': 'z', 'и': 'i', 'ј': 'j', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'ћ': 'ć', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'č', 'ш': 'š',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Ђ': 'Ђ', 'Е': 'E', 'Ж': 'Ž', 'З': 'Z', 'И': 'I', 'Ј': 'J', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'Ћ': 'Ć', 'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'C', 'Ч': 'Č', 'Ш': 'Š'
    }
    sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
    for key in sorted_keys:
        text = text.replace(key, mapping[key])
    return text

def get_chunk_text(payload):
    if not payload:
        return ""
    for key in ["sadrzaj", "tekst", "text", "page_content", "content", "body", "chunk"]:
        val = payload.get(key)
        if val and isinstance(val, str) and len(val.strip()) > 0:
            return str(val)
    vals = [str(v) for k, v in payload.items() if k not in ["type", "naziv_fajla", "ime_prezime", "funkcija"] and isinstance(v, str)]
    return "\n".join(vals)

def zaposleni_odgovara_upitu(zaposleni_payload, pitanje_low):
    ime = str(zaposleni_payload.get('ime_prezime', '')).strip()
    norm_ime = normalize_str(cir_to_lat(ime))
    delovi = norm_ime.split()
    if not delovi:
        return False
    
    ime_zaposlenog = delovi[0]
    koren_imena = ime_zaposlenog[:min(len(ime_zaposlenog), 4)]
    
    if koren_imena in pitanje_low:
        if len(delovi) > 1:
            prezime_u_pitanju = any(d in pitanje_low for d in delovi[1:])
            if prezime_u_pitanju or len(pitanje_low.split()) <= 6:
                return True
        else:
            return True
    return False

def cisti_odgovor(tekst):
    if not tekst:
        return ""
    # Ukloni sve moguće varijacije think tagova i unutrašnjosti
    tekst = re.sub(r'<think>.*?</think>', '', tekst, flags=re.DOTALL | re.IGNORECASE)
    tekst = re.sub(r'</?think>', '', tekst, flags=re.IGNORECASE)
    # Ako slučajno ostane zaostao nezavršen tag, očisti sve pre njega
    if '<think>' in tekst.lower():
        delovi = re.split(r'<think>', tekst, flags=re.IGNORECASE)
        tekst = delovi[-1]
    return tekst.strip()

def pozovi_llm(prompt, temperatura=0.1):
    # Provereni modeli koji NE PIŠU razmišljanje (nema Qwena ni reasoning modela)
    modeli = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]
    
    for model in modeli:
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "Ti si stručni asistent Biroa. Odgovaraj ISKLJUČIVO na srpskom jeziku, direktno, sažeto i precizno. Koristi isključivo ispravnu i tačnu stručnu terminologiju. Strogo je zabranjeno pisanje bilo kakvog razmišljanja, uvodnih fraza, pozdrava ili engleskog teksta."
                    },
                    {"role": "user", "content": prompt}
                ],
                model=model,
                temperature=temperatura,
                max_tokens=2048
            )
            sirovi_odgovor = chat_completion.choices[0].message.content or ""
            odgovor = cisti_odgovor(sirovi_odgovor)
            
            if not odgovor.strip():
                continue
            return f"{odgovor}\n\n*(Generisano pomoću: {model})*"
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "rate_limit" in err_msg or "404" in err_msg or "not_found" in err_msg or "400" in err_msg or "decommissioned" in err_msg:
                time.sleep(1)
                continue 
            return f"Došlo je do greške (Model {model}): {str(e)}"
            
    return "Svi AI modeli su trenutno opterećeni (dostignut je limit besplatnih tokena u minuti - Rate Limit). Molimo sačekajte oko 60 sekundi i pokušajte ponovo."

def daj_sliku_zaposlenog(z):
    ime = str(z.get('ime_prezime', '')).strip()
    if not ime:
        return None
    varijante = [
        ime.replace(' ', '_') + ".jpg",
        normalize_str(ime).replace(' ', '_') + ".jpg",
        cir_to_lat(ime).replace(' ', '_') + ".jpg"
    ]
    for var in set(varijante):
        url = f"{R2_BASE_URL}/{urllib.parse.quote(var)}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return url
        except Exception:
            continue
    return f"{R2_BASE_URL}/{urllib.parse.quote(varijante[0])}"

def tavily_search(query):
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return "Tavily API ključ nije podešen u .env fajlu."
    
    url = "https://api.tavily.com/search"
    payload = json.dumps({
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 3
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url, 
        data=payload, 
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }, 
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get("results", [])
            snippets = [r.get("content", "") for r in results]
            return "\n".join(snippets)
    except Exception as e:
        return f"Greška pri pretrazi interneta: {str(e)}"

class AgentState(TypedDict):
    pitanje: str
    odgovor: str
    povezani_zaposleni: List[Any]

def router_node(state: AgentState):
    pitanje_low = state["pitanje"].lower()
    web_reci = ["ministar", "ministri", "ministarka", "vreme", "prognoza", "vesti", "najnovije", "sport", "predsednik vlade", "ministarstvo", "zdravlja", "privrede", "vlada"]
    
    if any(w in pitanje_low for w in web_reci):
        return "web_node"
    return "rag_node"

def rag_node(state: AgentState):
    pitanje = state["pitanje"]
    pitanje_low = normalize_str(cir_to_lat(pitanje))
    
    kontekst_lista = []
    svi_zaposleni, svi_dokumenti = ucitaj_podatke_iz_baze()

    direktori_zaposleni = []
    zamenici_zaposleni = []
    svi_imena_funkcije = []
    zaposleni_u_pitanju = []

    for p in svi_zaposleni:
        ime = str(p.get('ime_prezime', '')).strip()
        funkcija = str(p.get('funkcija', '')).strip()
        opis = str(p.get('opis', '')).strip()
        svi_imena_funkcije.append(f"- {ime} ({funkcija})")
        
        if zaposleni_odgovara_upitu(p, pitanje_low):
            zaposleni_u_pitanju.append(p)

        funkcija_low = funkcija.lower()
        opis_low = opis.lower()
        
        if "direktor" in funkcija_low or "direktor" in opis_low:
            if "zamenik" in funkcija_low or "zamenik" in opis_low:
                zamenici_zaposleni.append(f"{ime} - {funkcija}")
            else:
                direktori_zaposleni.append(f"{ime} - {funkcija}")

    is_zamenik_query = any(w in pitanje_low for w in ["zamenik", "zamenici"])
    is_direktor_query = any(w in pitanje_low for w in ["direktor", "ko je direktor"])
    is_spisak_query = any(w in pitanje_low for w in ["spisak", "svi zaposleni", "ko sve radi", "lista zaposlenih", "svi radnici"])
    
    if direktori_zaposleni and is_direktor_query and not is_zamenik_query:
        kontekst_lista.append("DIREKTOR BIROA:\n" + "\n".join(direktori_zaposleni))
    if zamenici_zaposleni and is_zamenik_query:
        kontekst_lista.append("ZAMENICI DIREKTORA:\n" + "\n".join(zamenici_zaposleni))
        
    if any(w in pitanje_low for w in ["zaposlen", "ko radi", "ko sve", "spisak", "radnik", "ko je", "ima li", "postoji li"]) or zaposleni_u_pitanju:
        kontekst_lista.append("KOMPLETAN SPISAK SVIH ZAPOSLENIH U BIROU:\n" + "\n".join(svi_imena_funkcije))

    if any(w in pitanje_low for w in ["stampac", "toner", "kaset", "ploter", "oprema", "stampaci", "toneri"]):
        for pt in svi_dokumenti:
            sadrzaj = get_chunk_text(pt.payload)
            sadrzaj_lat = normalize_str(cir_to_lat(sadrzaj))
            if any(w in sadrzaj_lat for w in ["stampac", "toner", "ploter", "hp", "epson", "canon", "kyocera", "lexmark", "bizhub"]):
                naziv = pt.payload.get('naziv_fajla', 'Dokument')
                entry = f"Dokument ({naziv}): {sadrzaj}"
                if entry not in kontekst_lista:
                    kontekst_lista.append(entry)

    stop_words = {"daj", "podatke", "o", "za", "osnovu", "osnove", "osnova", "kako", "sta", "gde", "je", "su", "se", "i", "u", "na", "od", "do", "ima", "li", "prikazi", "navedi"}
    upit_reci = [w for w in re.findall(r'\b\w+\b', pitanje_low) if w not in stop_words and len(w) > 2]
    
    osnova_nazivi_reci = set()
    for pt in svi_dokumenti:
        nf = normalize_str(cir_to_lat(pt.payload.get('naziv_fajla', '')))
        if "gj" in nf or "osnova" in nf:
            for w in re.findall(r'\b\w+\b', nf):
                if len(w) > 2:
                    osnova_nazivi_reci.add(w)

    is_osnova_query = (
        any(w in pitanje_low for w in ["osnova", "osnove", "osnovu", "osnovi", "gazdins", "gj", "povrsina", "hektar", "ha", "ruza", "vetar", "vetrova", "klima"]) or
        any(w in osnova_nazivi_reci for w in upit_reci)
    )

    if is_osnova_query:
        for pt in svi_dokumenti:
            sadrzaj = get_chunk_text(pt.payload)
            sadrzaj_lat = normalize_str(cir_to_lat(sadrzaj))
            naziv_fajla = pt.payload.get('naziv_fajla', '')
            naziv_lat = normalize_str(cir_to_lat(naziv_fajla))
            
            poklapanje_naziva = any(rec in naziv_lat for rec in upit_reci)
            poklapanje_sadrzaja = any(rec in sadrzaj_lat for rec in upit_reci)
            je_osnova_fajl = "gj" in naziv_lat or "osnova" in naziv_lat
            
            if poklapanje_naziva or (poklapanje_sadrzaja and je_osnova_fajl):
                naziv = naziv_fajla if naziv_fajla else 'Dokument'
                entry = f"Dokument ({naziv}): {sadrzaj}"
                if entry not in kontekst_lista:
                    kontekst_lista.append(entry)

    clan_numbers = re.findall(r'\b\d+\b', pitanje_low)
    is_clan_query = any(w in pitanje_low for w in ["clan", "cl", "ugovor", "kolektivn"])

    if is_clan_query and clan_numbers:
        for broj in clan_numbers:
            matched_count = 0
            pattern = re.compile(rf'(?:clan|cl|clana|clanu)[\s\.\-_]*{broj}\b', re.IGNORECASE)
            
            for pt in svi_dokumenti:
                if matched_count >= 3:
                    break
                sadrzaj = get_chunk_text(pt.payload)
                sadrzaj_norm = normalize_str(cir_to_lat(sadrzaj))
                
                match = pattern.search(sadrzaj_norm)
                if match:
                    start_idx = max(0, match.start() - 50)
                    end_idx = min(len(sadrzaj), match.start() + 4000)
                    isechak = sadrzaj[start_idx:end_idx]
                    
                    naziv = pt.payload.get('naziv_fajla', 'Dokument')
                    entry = f"Dokument ({naziv}) - ISEČAK ČLANA {broj}:\n...{isechak}..."
                    
                    if entry not in kontekst_lista:
                        kontekst_lista.append(entry)
                        matched_count += 1

    try:
        vector = encoder.encode(pitanje).tolist()
        response = qdrant_client.query_points(collection_name="biro_baza", query=vector, limit=6)
        for res in response.points:
            payload = res.payload
            if payload.get("type") != "zaposleni":
                sadrzaj = get_chunk_text(payload)
                naziv = payload.get('naziv_fajla', 'Dokument')
                entry = f"Dokument ({naziv}): {sadrzaj}"
                if not any(sadrzaj[:50] in k for k in kontekst_lista):
                    kontekst_lista.append(entry)
    except Exception:
        pass
            
    kontekst_lista = kontekst_lista[:8]
    kontekst = "\n---\n".join(kontekst_lista)
    
    if len(kontekst) > 8000:
        kontekst = kontekst[:8000] + "\n...[ostatak teksta skraćen]"

    if not kontekst.strip():
        kontekst = "Nema pronađenog konteksta u bazi."
    
    prompt = f"""Na osnovu priloženog konteksta odgovori precizno na pitanje na srpskom jeziku. Koristi isključivo ispravnu i tačnu stručnu terminologiju.

PRAVILA:
1. Odgovori DIREKTNO, POTPUNO i TAČNO. Zabranjeno je razmišljanje naglas i engleski jezik.
2. Ako se postavlja pitanje da li neka osoba postoji u bazi, proveri spisak u kontekstu i odgovori jasno.
3. Ako u kontekstu nema traženog podatka, jasno navedi: "Traženi podatak nije pronađen u arhivi."

Kontekst:
{kontekst}

Pitanje: {pitanje}"""
    
    odgovor = pozovi_llm(prompt)
    
    povezani_zaposleni = []
    is_employee_query = (
        is_direktor_query or 
        is_zamenik_query or 
        is_spisak_query or 
        bool(zaposleni_u_pitanju) or
        any(w in pitanje_low for w in ["zaposlen", "ko radi", "ko sve", "radnik", "ima li", "postoji li"])
    )

    if is_employee_query:
        if is_direktor_query and not is_zamenik_query:
            for z in svi_zaposleni:
                f_low = str(z.get('funkcija', '')).lower()
                o_low = str(z.get('opis', '')).lower()
                if ("direktor" in f_low or "direktor" in o_low) and not ("zamenik" in f_low or "zamenik" in o_low):
                    if z not in povezani_zaposleni:
                        povezani_zaposleni.append(z)
        elif is_zamenik_query:
            for z in svi_zaposleni:
                f_low = str(z.get('funkcija', '')).lower()
                o_low = str(z.get('opis', '')).lower()
                if "zamenik" in f_low or "zamenik" in o_low:
                    if z not in povezani_zaposleni:
                        povezani_zaposleni.append(z)
        elif is_spisak_query:
            povezani_zaposleni = list(svi_zaposleni)
        elif zaposleni_u_pitanju:
            povezani_zaposleni = list(zaposleni_u_pitanju)
        else:
            odgovor_norm = normalize_str(odgovor)
            for z in svi_zaposleni:
                if zaposleni_odgovara_upitu(z, odgovor_norm):
                    if z not in povezani_zaposleni:
                        povezani_zaposleni.append(z)
                
    return {"odgovor": odgovor, "povezani_zaposleni": povezani_zaposleni}

def web_node(state: AgentState):
    pitanje = state["pitanje"]
    rezultati_tekst = tavily_search(pitanje)
    
    prompt = f"""Odgovori tačno, precizno i jasno na srpskom jeziku na sledeće pitanje, koristeći informacije sa interneta u nastavku:

Internet rezultati:
{rezultati_tekst}

Pitanje: {pitanje}"""
    
    odgovor = pozovi_llm(prompt)
    return {"odgovor": odgovor, "povezani_zaposleni": []}

workflow = StateGraph(AgentState)
workflow.add_node("rag_node", rag_node)
workflow.add_node("web_node", web_node)
workflow.set_conditional_entry_point(router_node, {"web_node": "web_node", "rag_node": "rag_node"})
workflow.add_edge("rag_node", END)
workflow.add_edge("web_node", END)
agent = workflow.compile()

# --- STREAMLIT UI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.image(LOGO_SRBIJASUME_URL, width=200)
    st.image(LOGO_BIRO_URL, width=150)
    
    st.markdown("### Kontrole")
    if st.button("🗑️ Obriši sve odgovore", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("### Tipična pitanja")
    pitanja = [
        "Ko je direktor Biroa?",
        "Ko su zamenici direktora?",
        "Ko su zaposleni u Birou?",
        "Postoji li zaposleni Nenad?",
        "Ima li Bojane Jelić u bazi Biroa?",
        "Daj osnovne podatke o Osnovi za Crni vrh.",
        "Daj podatke za osnovu Vranjača?",
        "Koje vrste štampača se koriste u Birou?",
        "Koji toneri se koriste za štampače u Birou?",
        "Koji je član 14 Kolektivnog ugovora?",
        "Ko je ministar zdravlja Srbije?"
    ]
    
    for p in pitanja:
        if st.button(p, use_container_width=True):
            st.session_state.brzi_unos = p

st.title("🌲 Biro AI Agent (Powered by LangGraph)")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("zaposleni"):
            st.markdown("---")
            cols = st.columns(min(max(len(msg["zaposleni"]), 1), 4))
            for idx, z in enumerate(msg["zaposleni"]):
                with cols[idx % 4]:
                    img = daj_sliku_zaposlenog(z)
                    if img:
                        st.image(img, width=120)
                    st.markdown(f"**{z.get('ime_prezime')}**\n\n*{z.get('funkcija')}*")

user_input = st.chat_input("Unesi svoje pitanje ovde...")
pitanje = st.session_state.get("brzi_unos", user_input)

if pitanje:
    if "brzi_unos" in st.session_state:
        del st.session_state["brzi_unos"]
        
    with st.chat_message("user"):
        st.write(pitanje)
    st.session_state.messages.append({"role": "user", "content": pitanje})
    
    with st.chat_message("assistant"):
        with st.spinner("Agent razmišlja..."):
            rezultat = agent.invoke({"pitanje": pitanje, "odgovor": "", "povezani_zaposleni": []} )
            
            odgovor = rezultat["odgovor"]
            zaposleni = rezultat["povezani_zaposleni"]
            
            st.write(odgovor)
            
            if zaposleni:
                st.markdown("---")
                cols = st.columns(min(max(len(zaposleni), 1), 4))
                for idx, z in enumerate(zaposleni):
                    with cols[idx % 4]:
                        img = daj_sliku_zaposlenog(z)
                        if img:
                            st.image(img, width=120)
                        st.markdown(f"**{z.get('ime_project')}**" if "ime_project" in z else f"**{z.get('ime_prezime')}**\n\n*{z.get('funkcija')}*")
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": odgovor,
                "zaposleni": zaposleni
            })