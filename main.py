def puxar_proxies_da_api():
    """Tenta buscar proxies gratuitas. Se falhar, retorna uma lista vazia sem quebrar o script."""
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all"
    print("🌐 Tentando carregar proxies frescas da API pública...", end="", flush=True)
    
    try:
        # Timeout curto (5s) para o script não ficar travado se a API estiver lenta
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            proxies = [p.strip() for p in r.text.split("\r\n") if p.strip()]
            print(f" ✅ {len(proxies)} proxies carregadas com sucesso!")
            return proxies
        else:
            print(f" ⚠️ API respondeu com status {r.status_code}. Usando IP local.")
    except Exception as e:
        # Captura qualquer erro de rede, queda da API ou DNS sem derrubar o programa
        print(" ⚠️ Falha ao conectar na API de proxies (Timeout/Queda). Usando IP local.")
    
    return []

def main():
    # Adicionado flush=True aqui para forçar o Railway a mostrar o início imediatamente
    print("🎯 Discord Finder — 4 letras + Logs do Railway", flush=True)
    print("=" * 50, flush=True)
    print(f"Caracteres: {CHARS}", flush=True)
    print(f"Combinações possíveis: {len(CHARS)**TAMANHO:,}", flush=True)
    
    # ─── LOGICA DE CARREGAMENTO SEGURA ───
    global PROXIES_LISTA
    if os.getenv("PROXIES_LISTA"):
        # 1ª Opção: Se você configurou proxies fixas no Railway, usa elas
        PROXIES_LISTA = [p.strip() for p in os.getenv("PROXIES_LISTA").split(",") if p.strip()]
        print(f"⚙️ Usando proxies das variáveis de ambiente: {len(PROXIES_LISTA)}")
    else:
        # 2ª Opção: Tenta buscar da API. Se falhar, PROXIES_LISTA vira [] e roda no IP local
        PROXIES_LISTA = puxar_proxies_da_api()
    
    if not PROXIES_LISTA:
        print("ℹ️  Nenhum proxy disponível. As requisições usarão o IP local diretamente.")
    # ─────────────────────────────────────
    
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
