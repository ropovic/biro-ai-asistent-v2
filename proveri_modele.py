from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq()

def listaj_modele():
    print("Dostupni modeli na tvom nalogu:\n")
    models = client.models.list()
    for model in models.data:
        print(f"- {model.id}")

if __name__ == "__main__":
    listaj_modele()