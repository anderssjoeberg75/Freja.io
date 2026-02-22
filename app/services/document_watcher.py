import os
import time
import asyncio
import logging
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.core.config import BASE_DIR
from skills.document_analysis.tools import ingest_document_impl

logger = logging.getLogger(__name__)

KB_DIR = os.path.join(BASE_DIR, "docs", "knowledge_base")
LEARNINGS_DIR = os.path.join(BASE_DIR, ".learnings")

class DocumentIngestionHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.loop = loop

    def on_created(self, event):
        if event.is_directory:
            return
        self._process_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._process_file(event.src_path)

    def _process_file(self, filepath: str):
        if not (filepath.lower().endswith(".pdf") or filepath.lower().endswith(".txt") or filepath.lower().endswith(".md")):
            return
        
        filename = os.path.basename(filepath)
        logger.info(f"[DocumentWatcher] Detected new or modified document: {filename}. Waiting for transfer to complete...")
        
        def run_ingestion():
            # Wait to ensure the file is fully written before processing
            time.sleep(2)
            try:
                # Run the ingestion async function from our loop
                future = asyncio.run_coroutine_threadsafe(ingest_document_impl(filepath), self.loop)
                result = future.result()
                logger.info(f"[DocumentWatcher] Ingestion result for {filename}: {result}")
            except Exception as e:
                logger.error(f"[DocumentWatcher] Error ingesting {filename}: {e}", exc_info=True)
                
        # Start a short-lived thread to avoid blocking the watchdog observer thread
        Thread(target=run_ingestion, daemon=True).start()

class DocumentWatcher:
    def __init__(self):
        self.observer = None
        self.thread = None
        
    def start(self):
        if not os.path.exists(KB_DIR):
            os.makedirs(KB_DIR, exist_ok=True)
        if not os.path.exists(LEARNINGS_DIR):
            os.makedirs(LEARNINGS_DIR, exist_ok=True)
            
        loop = asyncio.get_running_loop()
        event_handler = DocumentIngestionHandler(loop)
        
        self.observer = Observer()
        self.observer.schedule(event_handler, KB_DIR, recursive=False)
        self.observer.schedule(event_handler, LEARNINGS_DIR, recursive=False)
        self.observer.start()
        logger.info(f"[DocumentWatcher] Started monitoring {KB_DIR} and {LEARNINGS_DIR} for new documents.")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("[DocumentWatcher] Stopped.")

document_watcher = DocumentWatcher()
