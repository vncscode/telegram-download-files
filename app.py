from telethon import TelegramClient 
import os
import uuid
import asyncio
import logging
import json
from rich.console import Console
from rich.progress import Progress

# Configuração do logging
logging.basicConfig(
    filename='app.log',  # Nome do arquivo de log
    filemode='w',  # Modo de arquivo 'w' para sobrescrever logs anteriores
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

diretorio_download = './clouds'
os.makedirs(diretorio_download, exist_ok=True)

console = Console()

CONFIG_FILE = "config.json"

def carregar_credenciais():
    """Carrega o api_id e o api_hash do arquivo de configuração"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def salvar_credenciais(api_id, api_hash):
    """Salva o api_id e o api_hash no arquivo de configuração"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'api_id': api_id, 'api_hash': api_hash}, f)

def solicitar_credenciais():
    """Solicita ao usuário o api_id e o api_hash com perguntas estilizadas"""
    api_id = console.input("[bold cyan]Digite seu [yellow]api_id[/yellow]: [/bold cyan]").strip()
    api_hash = console.input("[bold cyan]Digite seu [yellow]api_hash[/yellow]: [/bold cyan]").strip()
    salvar_credenciais(api_id, api_hash)
    return api_id, api_hash

def obter_credenciais():
    """Obtém as credenciais, solicitando-as ao usuário se necessário"""
    credenciais = carregar_credenciais()
    if credenciais:
        return credenciais['api_id'], credenciais['api_hash']
    else:
        return solicitar_credenciais()

def callback_progresso(atual, total):
    if total > 0:
        porcentagem = atual / total * 100
        mb_atual = atual / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        console.log(f"\rDownload: {mb_atual:.2f} MB de {mb_total:.2f} MB ({porcentagem:.2f}%)", end='')

def solicitar_extensoes():
    """Solicita ao usuário quais extensões de arquivo deseja baixar."""
    extensoes = console.input("[bold cyan]Digite as extensões de arquivo desejadas (ex: .txt, .pdf), separadas por vírgula: [/bold cyan]")
    return [ext.strip() for ext in extensoes.split(',')]

async def baixar_arquivos(cliente, nome_canal, extensoes):
    mensagens = [msg async for msg in cliente.iter_messages(nome_canal) if msg.file and msg.file.name and any(msg.file.name.endswith(ext) for ext in extensoes)]

    # Ordena as mensagens por tamanho do arquivo (do menor para o maior)
    mensagens.sort(key=lambda msg: msg.file.size if msg.file else float('inf'))

    total_arquivos = len(mensagens)

    if total_arquivos == 0:
        console.print(f"Nenhum arquivo encontrado no canal {nome_canal} com as extensões especificadas.", style="bold red")
        return

    console.print(f"[bold green]{total_arquivos} arquivos encontrados no canal {nome_canal} com as extensões especificadas.[/bold green]")

    # Cria uma pasta para o canal
    caminho_canal = os.path.join(diretorio_download, nome_canal.replace('@', ''))
    os.makedirs(caminho_canal, exist_ok=True)

    with Progress() as progress:
        tarefa = progress.add_task(f'Baixando arquivos de {nome_canal}', total=total_arquivos)

        for i, mensagem in enumerate(mensagens):
            nome_aleatorio = f"{uuid.uuid4()}{os.path.splitext(mensagem.file.name)[1]}"  # Mantém a extensão original
            caminho_arquivo = os.path.join(caminho_canal, nome_aleatorio)

            try:
                await mensagem.download_media(caminho_arquivo, progress_callback=callback_progresso)
                console.log(f"\nArquivo {i + 1}/{total_arquivos}: [bold blue]{nome_aleatorio}[/bold blue] baixado com sucesso!")
                logging.info(f"Arquivo {i + 1}/{total_arquivos} baixado com sucesso: {nome_aleatorio}")
            except Exception as e:
                console.log(f"[bold red]Erro ao baixar o arquivo {nome_aleatorio}: {e}[/bold red]")
                logging.error(f"Erro ao baixar o arquivo {nome_aleatorio}: {e}")

            progress.update(tarefa, advance=1)
            await asyncio.sleep(1)

async def main():
    os.system('cls' if os.name == 'nt' else 'clear')  # Limpa o terminal

    # Obter credenciais (api_id e api_hash)
    api_id, api_hash = obter_credenciais()

    # Inicializa o cliente do Telegram com as credenciais
    cliente = TelegramClient('vncscode_session', api_id, api_hash)
    await cliente.start()

    # Solicita ao usuário que insira ao menos um canal
    canais = []
    
    while True:
        canal = console.input("[bold cyan]Digite o nome de um canal (formato @canal) ou pressione Enter para finalizar: [/bold cyan]").strip()
        if not canal and canais:  # Se o usuário pressionar Enter e já houver ao menos um canal
            break
        elif canal:
            canais.append(canal)
        else:
            console.print("[bold red]Você deve fornecer pelo menos um canal.[/bold red]")

    # Solicita as extensões de arquivo desejadas
    extensoes = solicitar_extensoes()

    for canal in canais:
        console.print(f'[bold yellow]Baixando arquivos de {canal}...[/bold yellow]')
        await baixar_arquivos(cliente, canal, extensoes)

    console.print('[bold green]Download concluído![/bold green]')

if __name__ == '__main__':
    asyncio.run(main())

# @vncscode