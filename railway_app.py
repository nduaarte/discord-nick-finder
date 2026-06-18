import requests
import random
import string
import time
import itertools

# ─────────────────────────────────────────
#  CONFIGURAÇÃO — 3 CARACTERES, LETRAS+NUMEROS+. _
# ─────────────────────────────────────────
TAMANHO = 3
CHARS = string.ascii_lowercase + string.digits + "._"
DELAY = 2.0
MAX_TENTATIVAS = 10000
ARQUIVO_SAIDA = "nicks_3_simbolos.txt"

PROXIES_LISTA = [

]
# ─────────────────────────────────────────

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

_proxy_cycle = itertools.cycle(PROXIES_LISTA) if PROXIES_LISTA else None

def pegar_proxy():
    if not _proxy_cycle:
        return None
    p = next(_proxy_cycle)
    return {"http": p, "https": p}

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
    proxy = pegar_proxy()
    try:
        r = requests.post(url, json=payload, headers=HEADERS, proxies=proxy, timeout=15)
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
            print(f"  HTTP {r.status_code}", flush=True)
            return None
    except requests.exceptions.ProxyError as e:
        print(f"  ❌ Proxy erro: {e}", flush=True)
        return None
    except requests.RequestException as e:
        print(f"  ❌ Erro: {e}", flush=True)
        return None


def main():
    print("🎯 Discord Finder — 3 chars (Railway)")
    print("=" * 50)
    print(f"Caracteres: {CHARS}")
    print(f"Combinações possíveis: {len(CHARS)**TAMANHO:,}")
    print("=" * 50)
    print()

    testados = set()
    tentativas = 0
    encontrados = []

    while tentativas < MAX_TENTATIVAS:
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

        elif disponivel is False:
            print("❌ ocupado", flush=True)

        else:
            print("⚠️  erro", flush=True)

        time.sleep(DELAY)

    print()
    print("=" * 50)
    print(f"✔ Total: {len(encontrados)} nicks encontrados")
    if encontrados:
        print(f"Nicks: {encontrados}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Parado pelo usuário.")
