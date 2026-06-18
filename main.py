import requests
import random
import string
import time
import itertools
import os

# ─────────────────────────────────────────
#  CONFIGURAÇÃO — 3 CARACTERES, LETRAS+NUMEROS+. _
# ─────────────────────────────────────────
TAMANHO = 3
CHARS = string.ascii_lowercase + string.digits + "._"
DELAY = 2.0
ARQUIVO_SAIDA = "nicks_3_simbolos.txt"
ARQUIVO_TESTADOS = "testados_3_chars.txt"  # LOG DE JÁ TESTADOS

PROXIES_LISTA = []
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
    print("🎯 Discord Finder — 3 chars (sem repetir)")
    print("=" * 50)
    print(f"Caracteres: {CHARS}")
    print(f"Combinações possíveis: {len(CHARS)**TAMANHO:,}")
    print("=" * 50)
    
    # Carrega nicks já testados
    testados = carregar_testados()
    print(f"Nicks já testados: {len(testados)}")
    print()

    tentativas = 0
    encontrados = []

    while True:  # Loop infinito — roda até encontrar todos ou você parar
        nick = gerar_nick()
        
        # Pula se já foi testado
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
            # Também salva no log de testados
            salvar_testado(nick)

        elif disponivel is False:
            print("❌ ocupado", flush=True)
            # Salva mesmo que ocupado, pra não testar de novo
            salvar_testado(nick)

        else:
            print("⚠️  erro", flush=True)
            # Não salva se teve erro, pra tentar de novo depois

        time.sleep(DELAY)

        # Log a cada 100 tentativas
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
