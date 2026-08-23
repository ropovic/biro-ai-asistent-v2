from pathlib import Path
from pdfminer.high_level import extract_text

# Tačna putanja do prve Osnove gazdovanja
pdf_fajl = Path(r"D:\Dokumenti\osnove\1605_Donji PEK_2025-2026.pdf")

def probno_citanje_pdf(putanja):
    print(f"⏳ Započinjem čitanje fajla: {putanja.name}...\n")
    
    try:
        # extract_text čita ceo dokument
        ceo_tekst = extract_text(putanja)
        
        # Da ne bismo zagušili terminal, štampamo samo prvih 1500 karaktera
        print("--- POČETAK DOKUMENTA ---")
        print(ceo_tekst[:1500])
        print("\n--- (Prikazano je samo prvih 1500 karaktera) ---")
        
        # Prikazujemo ukupnu dužinu teksta čisto da vidimo koliko je veliki
        print(f"\n✅ Upešno pročitano! Dokument ima ukupno {len(ceo_tekst)} karaktera.")
        
    except Exception as e:
        print(f"❌ Došlo je do greške: {e}")

if __name__ == "__main__":
    # Provera da li fajl zaista postoji pre nego što ga otvorimo
    if pdf_fajl.exists():
        probno_citanje_pdf(pdf_fajl)
    else:
        print(f"Greška: Ne mogu da pronađem fajl na putanji {pdf_fajl}")