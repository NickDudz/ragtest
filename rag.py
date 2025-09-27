
from __future__ import annotations
import os, sys
import typer
from rich import print
from rich.table import Table
from ragtoolkit.pipeline import read_config, ingest_corpus, ask_question, save_answer

app = typer.Typer(add_completion=False, help="""
Local RAG Toolkit — ingest documents and ask questions with citations.
""")

def _load_cfg(config_path: str):
    if not os.path.isfile(config_path):
        print(f"[red]Config not found:[/red] {config_path}")
        raise typer.Exit(code=1)
    return read_config(config_path)

@app.command()
def ingest(config: str = typer.Option("rag.yaml", help="Path to config file")):
    """Parse, chunk, embed and index documents from [paths.data_dir]."""
    cfg = _load_cfg(config)
    stats = ingest_corpus(cfg)
    print(f"[green]Ingest complete[/green]: documents={stats['documents']} chunks={stats['chunks']}")

@app.command()
def ask(
    question: str = typer.Argument(..., help="Natural-language question"),
    config: str = typer.Option("rag.yaml", help="Path to config file"),
    save: bool = typer.Option(True, help="Save Markdown answer to outputs/"),
):
    """Ask a question using retrieval-augmented generation."""
    cfg = _load_cfg(config)
    answer, hits = ask_question(cfg, question)
    print("\n[bold]Answer[/bold]\n" + answer + "\n")
    if hits:
        table = Table(title="Sources", show_lines=False)
        table.add_column("ID", no_wrap=True)
        table.add_column("Source", no_wrap=True)
        table.add_column("Path", overflow="fold")
        table.add_column("Page", no_wrap=True)
        for i, h in enumerate(hits, 1):
            table.add_row(f"S{i}", h['meta'].get('source',''), h['meta'].get('path',''), str(h['meta'].get('page','')))
        print(table)
    if save:
        path = save_answer(cfg, question, answer, hits)
        print(f"[cyan]Saved to[/cyan] {path}")

@app.command()
def clear(
    really: bool = typer.Option(False, help="Set True to confirm index clear"),
    config: str = typer.Option("rag.yaml", help="Path to config file"),
):
    """Clear Chroma collection (keeps raw docs)."""
    if not really:
        print("[yellow]Refusing to clear without --really True[/yellow]")
        raise typer.Exit(code=1)
    from ragtoolkit.vectordb import get_or_create_collection
    from chromadb.utils import embedding_functions
    cfg = _load_cfg(config)
    col = get_or_create_collection(cfg.paths['storage_dir'], "rag")
    col.delete(where={})
    print("[green]Collection cleared.[/green]")

@app.command()
def export(
    last: bool = typer.Option(True, help="Export last answer only"),
    out: str = typer.Option("outputs/last_answer.md", help="Output path for markdown export"),
    config: str = typer.Option("rag.yaml", help="Path to config file"),
):
    """Stub for future export utilities (merging answers, etc.)."""
    # For now, just copy the most recent answer-*.md if present.
    cfg = _load_cfg(config)
    from glob import glob
    import shutil, os
    files = sorted(glob(os.path.join(cfg.paths['outputs_dir'], 'answer-*.md')))
    if not files:
        print("[yellow]No answers to export yet.[/yellow]")
        raise typer.Exit(code=1)
    src = files[-1]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copy2(src, out)
    print(f"[green]Exported[/green] {src} -> {out}")

@app.command()
def web(
    port: int = typer.Option(8000, help="Port to run web server on"),
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
):
    """Start the web interface server."""
    import uvicorn
    print(f"[green]Starting web server at[/green] http://{host}:{port}")
    print("[cyan]Press Ctrl+C to stop[/cyan]")
    uvicorn.run("web_server:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    app()
