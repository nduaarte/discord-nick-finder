import requests
import random
import string
import time
import os
import subprocess

# ─────────────────────────────────────────
#  CONFIGURAÇÃO — 3 CARACTERES, LETRAS+NUMEROS+. _
# ─────────────────────────────────────────
TAMANHO = 3
CHARS = string.ascii_lowercase + string.digits + "._"
DELAY = 2.0
ARQUIVO_SAIDA = "nicks_3_simbolos.txt"
ARQUIVO_TESTADOS = "testados_3_chars.txt"

# Token do GitHub (vai ser uma variável de ambiente no Railway)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = "seu_usuario/discord-nick-finder"  # MUDE PARA SEU USUARIO/REPO

PROXIES_LISTA = [
     "http://dauwberq:dq8inyg5ttsx@31.59.20.176:6754/",
    "http://dauwberq:dq8inyg5ttsx@92.113.242.158:6742/",
   "http://dauwberq:dq8inyg5ttsx@38.154.203.95:5863/" ,
   "http://dauwberq:dq8inyg5ttsx@198.105.121.200:6462/" ,
    "http://dauwberq:dq8inyg5ttsx@64.137.96.74:6641/" ,
     "http://dauwberq:dq8inyg5ttsx@38.154.185.97:6370/" ,
   "http://dauwberq:dq8inyg5ttsx@142.111.67.146:5611/" 
]
# ─────────────────────────────────────────

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def carregar_testados():
    """Carrega nicks já testados do arquivo"""
    if os.path.exists(ARQUIVO_TESTADOS):
        with open(ARQUIVO_TESTADOS, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def salvar_testado(nick):
    """Salva um nick testado no arquivo"""
    with open(ARQUIVO_TESTADOS, "a") as f:
        f.write(nick + "\n")

def fazer_commit_github(mensagem):
    """Faz commit e push dos arquivos para GitHub"""
    if not GITHUB_TOKEN:
        return False
    
    try:
        # Configura git
        os.system('git config --local user.email "railway@bot.com"')
        os.system('git config --local user.name "Railway Bot"')
        
        # Adiciona arquivos
        os.system('git add testados_3_chars.txt nicks_3_simbolos.txt')
        
        # Commit
        os.system(f'git commit -m "{mensagem}"')
        
        # Push com token
        os.system(f'git push https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git HEAD:main')
        
        print(f"  ☁️  Sincronizado no GitHub!", flush=True)
        return True
    except Exception as e:
        print(f"  ⚠️  Erro ao sincronizar: {e}", flush=True)
        return False

def gerar_senha():
    upper = random.choices(string.ascii_uppercase, k=4)
    lower = random.choices(string.ascii_lowercase, k=4)
    digits = random.choices(string.digits, k=4)
    special = random.choices("!@#$%^&*", k=4)
    all_chars = upper + lower + digits + special
    random.shuffle(all_chars)
    return "".join(all_chars)

def gerar_nick():
    while True:
        nick = "".join(random.choices(CHARS, k=TAMANHO))
        if nick[0] not in "._" and nick[-1] not in "._":
            return nick

def verificar_disponibilidade(username):
    url = "https://discord.com/api/v9/auth/register"
    payload = {
        "username": username,
        "email": f"check_{random.randint(100000,999999)}@tempcheck.invalid",
        "password": gerar_senha(),
        "date_of_birth": "2000-01-01",
        "consent": True
    }
    try:
        r = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        data = r.json()
        errors = str(data)

        if r.status_code == 200:
            return True
        elif "USERNAME_TOO_MANY_USERS" in errors or "username" in str(data.get("errors", {})):
            return False
        elif "email" in str(data.get("errors", {})) or "captcha" in errors.lower():
            return True
        elif r.status_code == 429:
            retry = float(r.headers.get("Retry-After", 5))
            print(f"  ⚠️  Rate limit! Aguardando {retry:.0f}s...", flush=True)
            time.sleep(retry)
            return None
        else:
            return None
    except requests.RequestException as e:
        print(f"  ❌ Erro: {e}", flush=True)
        return None


def main():
    print("🎯 Discord Finder — 3 chars + GitHub Sync")
    print("=" * 50)
    print(f"Caracteres: {CHARS}")
    print(f"Combinações possíveis: {len(CHARS)**TAMANHO:,}")
    print("=" * 50)
    
    testados = carregar_testados()
    print(f"Nicks já testados: {len(testados)}")
    print()

    tentativas = 0
    encontrados = []
    commits_pendentes = 0

    while True:
        nick = gerar_nick()
        
        if nick in testados:
            continue
        
        testados.add(nick)
        tentativas += 1

        print(f"[{tentativas:>5}] Testando: {nick} ... ", end="", flush=True)

        disponivel = verificar_disponibilidade(nick)

        if disponivel is True:
            print("✅ DISPONÍVEL!", flush=True)
            encontrados.append(nick)
            with open(ARQUIVO_SAIDA, "a") as f:
                f.write(nick + "\n")
            salvar_testado(nick)
            commits_pendentes += 1
            
            # Faz commit imediato quando encontra algo
            fazer_commit_github(f"🎉 Nick disponível encontrado: {nick}")
            commits_pendentes = 0

        elif disponivel is False:
            print("❌ ocupado", flush=True)
            salvar_testado(nick)
            commits_pendentes += 1

        else:
            print("⚠️  erro", flush=True)

        time.sleep(DELAY)

        # Commit a cada 200 testadas ou se tiver pendências
        if tentativas % 200 == 0 and commits_pendentes > 0:
            fazer_commit_github(f"📊 Progresso: {tentativas} testadas, {len(encontrados)} encontradas")
            commits_pendentes = 0

        if tentativas % 100 == 0:
            print(f"  📊 Progresso: {tentativas} testadas, {len(encontrados)} encontradas", flush=True)

    print()
    print("=" * 50)
    print(f"✔ Total: {len(encontrados)} nicks encontrados")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Parado pelo usuário.")
        # Faz último commit ao parar
        fazer_commit_github("⛔ Script parado manualmente")
