import requests
import random
import string
import time
import os
import redis

# ─────────────────────────────────────────
# CONFIGURAÇÃO — 4 CARACTERES, APENAS LETRAS
# ─────────────────────────────────────────
TAMANHO = 4
CHARS = string.ascii_lowercase  # Apenas letras minúsculas (a-z)
DELAY = 2.0

# Conexão Automática com o Redis do Railway para lembrar dos nicks já testados
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    db = redis.Redis.from_url(REDIS_URL, decode_responses=True)
else:
    db = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Lista de Proxies (Lê do ambiente se configurado, senão usa a padrão)
if os.getenv("PROXIES_LISTA"):
    PROXIES_LISTA = [p.strip() for p in os.getenv("PROXIES_LISTA").split(",") if p.strip()]
else:
    PROXIES_LISTA = [
        "http://rzvhgrsr:551w6d36l0fb@31.59.20.176:6754",
        "http://rzvhgrsr:551w6d36l0fb@31.56.127.193:6754",
        "http://rzvhgrsr:551w6d36l0fb@45.38.107.97:6754",
        "http://rzvhgrsr:551w6d36l0fb@38.154.203.95:6754",
        "http://rzvhgrsr:551w6d36l0fb@198.105.121.200:6754",
        "http://rzvhgrsr:551w6d36l0fb@64.137.96.74:6754",
        "http://rzvhgrsr:551w6d36l0fb@198.23.243.226:6754",
        "http://rzvhgrsr:551w6d36l0fb@38.154.185.97:6754",
        "http://rzvhgrsr:551w6d36l0fb@142.111.67.146:6754",
        "http://rzvhgrsr:551w6d36l0fb@191.96.254.138:6754"
    ]
# ─────────────────────────────────────────

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def gerar_senha():
    upper = random.choices(string.ascii_uppercase, k=4)
    lower = random.choices(string.ascii_lowercase, k=4)
    digits = random.choices(string.digits, k=4)
    special = random.choices("!@#$%^&*", k=4)
    all_chars = upper + lower + digits + special
    random.shuffle(all_chars)
    return "".join(all_chars)

def gerar_nick():
    return "".join(random.choices(CHARS, k=TAMANHO))

def verificar_disponibilidade(username, proxy_url=None):
    url = "https://discord.com/api/v9/auth/register"
    payload = {
        "username": username,
        "email": f"check_{random.randint(100000,999999)}@tempcheck.invalid",
        "password": gerar_senha(),
        "date_of_birth": "2000-01-01",
        "consent": True
    }
    
    proxies_config = {
        "http": proxy_url,
        "https": proxy_url
    } if proxy_url else None

    try:
        r = requests.post(url, json=payload, headers=HEADERS, proxies=proxies_config, timeout=10)
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
            origem = "no IP do Proxy" if proxy_url else "no seu IP Local"
            print(f"  ⚠️  Rate limit {origem}! (Bloqueio de {retry:.0f}s)", end="", flush=True)
            if not proxy_url:
                time.sleep(retry)
            return None
        else:
            return None
    except requests.RequestException:
        origem = "no proxy" if proxy_url else "na conexão local"
        print(f"  ❌ Erro de conexão {origem}", end="", flush=True)
        return None

def main():
    print("🎯 Discord Finder — 4 letras + Logs do Railway")
    print("=" * 50)
    print(f"Caracteres: {CHARS}")
    print(f"Combinações possíveis: {len(CHARS)**TAMANHO:,}")
    print(f"Proxies carregados: {len(PROXIES_LISTA)}")
    if not PROXIES_LISTA:
        print("ℹ️  Nenhum proxy configurado. As requisições usarão o IP local.")
    
    try:
        total_testados_inicial = db.scard("discord:4letras:testados")
        total_achados_inicial = db.scard("discord:4letras:disponiveis")
        print(f"🔗 Conectado ao Redis! {total_testados_inicial} conhecidos | {total_achados_inicial} já encontrados.")
    except redis.RedisError as e:
        print(f"🚨 Erro crítico ao conectar no Redis: {e}")
        return
        
    print("=" * 50)
    print()

    tentativas_sessao = 0

    while True:
        nick = gerar_nick()
        
        if db.sismember("discord:4letras:testados", nick):
            continue
        
        print(f"[{tentativas_sessao+1:>5}] Testando: {nick} ... ", end="", flush=True)

        proxy_atual = random.choice(PROXIES_LISTA) if PROXIES_LISTA else None
        disponivel = verificar_disponibilidade(nick, proxy_atual)

        if disponivel is True:
            tentativas_sessao += 1
            print(" ✨🎉 ✅ DISPONÍVEL! ✅ 🎉✨", flush=True)
            
            # SALVA EM AMBOS: No histórico geral e na lista de conquistas
            db.sadd("discord:4letras:testados", nick)
            db.sadd("discord:4letras:disponiveis", nick)
            time.sleep(DELAY)

        elif disponivel is False:
            tentativas_sessao += 1
            print(" ❌ ocupado", flush=True)
            db.sadd("discord:4letras:testados", nick)
            time.sleep(DELAY)

        else:
            se_com_proxy = "e alternando proxy imediatamente..." if PROXIES_LISTA else "e aguardando rate limit..."
            print(f" -> 🔄 Pulando {se_com_proxy}", flush=True)

        if tentativas_sessao > 0 and tentativas_sessao % 10 == 0 and disponivel is not None:
            total_geral = db.scard("discord:4letras:testados")
            total_sucessos = db.scard("discord:4letras:disponiveis")
            print(f"  📊 Progresso: {total_geral} testados | ⭐ {total_sucessos} DISPONÍVEIS salvos.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Parado pelo usuário.")
