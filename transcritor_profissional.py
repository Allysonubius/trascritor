# =========================
# APP TRANSCRITOR
# =========================

import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import subprocess
import sys
import threading
import torch
import numpy as np
from faster_whisper import WhisperModel
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import ffmpeg

# =========================
# CONFIG - MODEL_SIZE
# =========================
# large-v3  🥇 (melhor de todos)
# large-v2
# medium
# small
# base
# tiny

MODEL_SIZE = "large-v3" 
MAX_WORKERS = 1  


# Detecta GPU e tipo de cálculo
def detectar_device():
    if torch.cuda.is_available():
        return "cuda", "float16"
    else:
        return "cpu", "int8"


DEVICE, COMPUTE_TYPE = detectar_device()

# =========================
# APP
# =========================


class TranscritorPro:

    def __init__(self, root):
        self.root = root
        self.root.title("Transcritor de videos")
        largura = self.root.winfo_screenwidth()
        altura = self.root.winfo_screenheight()

        self.root.geometry(f"{largura}x{altura}")
        self.root.state("zoomed")

        # 🔥 ATRIBUTOS
        self.modelo_pronto = False
        self.model = None
        self.cancelar = False
        self.videos = []
        self.video_widgets = {}
        self.inicio_global = None
        self.video_atual = None

        self.aplicar_dark_mode()
        self.criar_interface()

        # Label de status do modelo
        self.label_modelo = tk.Label(
            self.root, text="Carregando modelo...", bg="#1e1e1e", fg="orange"
        )
        self.label_modelo.pack()

        threading.Thread(target=self.carregar_modelo, daemon=True).start()
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    # =========================
    # DARK MODE
    # =========================
    def carregar_modelo(self):
        self.model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        self.modelo_pronto = True
        self.root.after(
            0, lambda: self.label_modelo.config(text="Modelo carregado ✔", fg="#00ff88")
        )

    def aplicar_dark_mode(self):
        style = ttk.Style()
        style.theme_use("clam")
        # estilo base
        style.configure(
            "Dark.TButton",
            background="#2d2d2d",
            foreground="white",
            borderwidth=1,
            focusthickness=3,
            focuscolor="none",
        )

        # 🔥 hover / ativo
        style.map(
            "Dark.TButton",
            background=[
                ("active", "#3a3a3a"),  # mouse em cima
                ("pressed", "#555555"),  # clicando
            ],
            foreground=[("active", "white"), ("pressed", "white")],
        )
        style.configure("TProgressbar", troughcolor="#2d2d2d", background="#00ff88")
        self.root.configure(bg="#1e1e1e")

    def instalar_dependencias(self):
        import subprocess
        import sys
        import threading

        def verificar_dependencias():
            try:
                import torch
                import faster_whisper
                import reportlab
                import ffmpeg

                return True
            except:
                return False

        def run_install():
            try:
                if verificar_dependencias():
                    self.root.after(
                        0,
                        lambda: messagebox.showinfo(
                            "Info", "Dependências já instaladas!"
                        ),
                    )
                    return

                pacotes = [
                    "reportlab>=3.5.12",
                    "ffmpeg-python==0.2.0",
                    "torch",
                    "faster-whisper",
                ]

                for p in pacotes:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", p])

                self.root.after(
                    0,
                    lambda: messagebox.showinfo("Sucesso", "Dependências instaladas!"),
                )

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))

        threading.Thread(target=run_install, daemon=True).start()

    # =========================
    # INTERFACE
    # =========================
    def criar_interface(self):

        # ===== TOPO =====
        top = tk.Frame(self.root, bg="#1e1e1e")
        top.pack(fill="x", pady=5)
        self.linha_selecionada = None

        ttk.Button(top, text="Selecionar Pasta", command=self.selecionar_pasta).pack(
            side="left", padx=5
        )

        self.btn_iniciar = ttk.Button(top, text="Iniciar", command=self.iniciar)
        self.btn_iniciar.pack(side="left", padx=5)

        self.btn_cancelar = tk.Button(
            top,
            text="Cancelar",
            command=self.cancelar_processamento,
            bg="#444",
            fg="white",
        )
        self.btn_cancelar.pack(side="left", padx=5)

        ttk.Button(
            top, text="🔧 Instalar/Reparar", command=self.instalar_dependencias
        ).pack(side="left", padx=5)

        self.label_eta = tk.Label(self.root, text="", bg="#1e1e1e", fg="#00ff88")
        self.label_eta.pack()

        # ===== CONTAINER PRINCIPAL =====
        main = tk.Frame(self.root, bg="#1e1e1e")
        main.pack(fill="both", expand=True)
        for i in range(2):
            main.columnconfigure(i, weight=1)
        for i in range(2):
            main.rowconfigure(i, weight=1)

        # =========================
        # 1️⃣ LISTA DE VÍDEOS
        # =========================
        self.frame_lista = tk.Frame(main, bg="#1e1e1e")
        self.frame_lista.grid(row=0, column=0, sticky="nsew")

        self.frame_canvas_scroll = tk.Frame(self.frame_lista, bg="#1e1e1e")
        self.frame_canvas_scroll.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.frame_canvas_scroll, bg="#1e1e1e", highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.lista_interna = tk.Frame(self.canvas, bg="#1e1e1e")
        self.canvas.create_window((0, 0), window=self.lista_interna, anchor="nw")
        self.lista_interna.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def ativar_scroll(event):
            self.canvas.bind_all("<MouseWheel>", on_mousewheel)
            self.canvas.bind_all("<Button-4>", on_mousewheel)
            self.canvas.bind_all("<Button-5>", on_mousewheel)

        def desativar_scroll(event):
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

        self.canvas.bind("<Enter>", ativar_scroll)
        self.canvas.bind("<Leave>", desativar_scroll)

        # =========================
        # 2️⃣ INFORMAÇÕES DO VÍDEO
        # =========================
        self.frame_info = tk.Frame(main, bg="#2a2a2a")
        self.frame_info.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.info_text = tk.Text(
            self.frame_info, bg="#2a2a2a", fg="white", state="disabled", cursor="arrow"
        )
        self.info_text.pack(fill="both", expand=True, padx=5, pady=5)

        # =========================
        # 3️⃣ TRANSCRIÇÃO AO VIVO
        # =========================
        self.frame_transcricao = tk.Frame(main, bg="#111111")
        self.frame_transcricao.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.transcricao = tk.Text(
            self.frame_transcricao,
            bg="#111111",
            fg="#00ff88",
            state="disabled",
            cursor="arrow",
            bd=0,
            highlightthickness=0,
            relief="flat",
        )
        self.transcricao.pack(fill="both", expand=True, padx=5, pady=5)

        # =========================
        # 4️⃣ ACOMPANHAMENTO DETALHADO
        # =========================
        self.frame_detalhe = tk.Frame(main, bg="#2a2a2a")
        self.frame_detalhe.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.info_video_text = tk.Text(
            self.frame_detalhe, bg="#2a2a2a", state="disabled", fg="white"
        )
        self.info_video_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Label tempo minimalista
        self.label_tempo = tk.Label(
            self.root, text="", bg="#1e1e1e", fg="#00ff88", font=("Consolas", 10)
        )
        self.label_tempo.pack(pady=2)

    def selecionar_linha(self, video):
        # remove destaque anterior
        if hasattr(self, "linha_selecionada") and self.linha_selecionada:
            self.linha_selecionada.config(bg="#1e1e1e")

        linha = self.video_widgets[video]["linha"]

        # aplica destaque
        linha.config(bg="#333333")

        self.linha_selecionada = linha

    def mostrar_loading(self):

        if hasattr(self, "loading_overlay"):
            return

        self.loading_overlay = tk.Frame(self.frame_lista, bg="#1e1e1e")
        self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        # spinner (progressbar indeterminado)
        self.loading_bar = ttk.Progressbar(
            self.loading_overlay, mode="indeterminate", length=120
        )
        self.loading_bar.place(relx=0.5, rely=0.5, anchor="center")

        self.loading_bar.start(10)

    def esconder_loading(self):
        if hasattr(self, "loading_overlay"):
            self.loading_bar.stop()
            self.loading_overlay.destroy()
            del self.loading_overlay

    def on_click_video(self, video):

        if hasattr(self, "processando") and self.processando:
            messagebox.showwarning(
                "Processando",
                "Já existe um vídeo em processamento.\nCancele ou aguarde.",
            )
            return

        if getattr(self, "video_selecionado", None) == video:
            return

        # remove destaque anterior
        if hasattr(self, "video_selecionado") and self.video_selecionado:
            self.video_widgets[self.video_selecionado]["linha"].config(bg="#1e1e1e")

        # aplica destaque novo
        self.video_widgets[video]["linha"].config(bg="#333333")

        self.video_selecionado = video
        self.video_atual = video

        # 🔥 LIMPA TRANSCRIÇÃO
        self.transcricao.config(state="normal")
        self.transcricao.delete("1.0", tk.END)
        self.transcricao.config(state="disabled")

        # 🔥 LIMPA PAINEL DETALHE
        self.info_video_text.config(state="normal")
        self.info_video_text.delete("1.0", tk.END)
        self.info_video_text.config(state="disabled")

        self.mostrar_info(video)

    # =========================
    # SELEÇÃO DE VÍDEOS
    # =========================
    def selecionar_pasta(self):
        self.linha_selecionada = None
        pasta = filedialog.askdirectory()
        if not pasta:
            return
        self.videos.clear()
        self.video_widgets.clear()
        for widget in self.lista_interna.winfo_children():
            widget.destroy()

        FORMATS = [".mp4", ".mp3", ".m4a", ".wav", ".flac"]
        for raiz, _, files in os.walk(pasta):
            for f in files:
                if os.path.splitext(f)[1].lower() in FORMATS:
                    self.videos.append(os.path.join(raiz, f))

        if not self.videos:
            messagebox.showwarning(
                "Aviso", "Nenhum arquivo compatível encontrado na pasta."
            )
            return

        for i, video in enumerate(self.videos):
            linha = tk.Frame(self.lista_interna, bg="#1e1e1e", height=40)
            linha.grid(row=i, column=0, sticky="ew", padx=10, pady=3)
            linha.grid_propagate(False)

            var = tk.BooleanVar()
            tk.Checkbutton(
                linha, variable=var, bg="#1e1e1e", activebackground="#1e1e1e"
            ).pack(side="left", padx=(5, 10))

            nome = os.path.basename(video)
            lbl_nome = tk.Label(
                linha,
                text=(nome[:45] + "..." if len(nome) > 48 else nome).ljust(50, "."),
                bg="#1e1e1e",
                fg="white",
                anchor="w",
                font=("Consolas", 10),
            )
            lbl_nome.pack(side="left")
            lbl_nome.bind("<Button-1>", lambda e, v=video: self.on_click_video(v))

            status = tk.Label(
                linha,
                text="Aguardando".ljust(12),
                bg="#1e1e1e",
                fg="gray",
                width=12,
                anchor="w",
                font=("Consolas", 10),
            )
            status.pack(side="left", padx=10)

            progress = ttk.Progressbar(linha, length=200, mode="determinate")
            progress.pack(side="left", padx=5)

            lbl_percent = tk.Label(
                linha,
                text="0%",
                bg="#1e1e1e",
                fg="#00ff88",
                width=5,
                anchor="w",
                font=("Consolas", 10),
            )
            lbl_percent.pack(side="left", padx=5)

            self.video_widgets[video] = {
                "checkbox": var,
                "progress": progress,
                "status": status,
                "percent": lbl_percent,
                "linha": linha,
            }

        self.lista_interna.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)

    # =========================
    # MOSTRAR INFO DO VÍDEO
    # =========================
    def mostrar_info(self, video):
        self.video_atual = video
        tamanho = os.path.getsize(video) / (1024 * 1024)

        info = f"""
            Arquivo: {os.path.basename(video)}
            Caminho: {video}
            Tamanho: {tamanho:.2f} MB
            Status: {self.video_widgets[video]['status'].cget('text')}
            """

        self.info_text.config(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, info)
        self.info_text.config(state="disabled")

    # =========================
    # PROCESSAMENTO
    # =========================
    def txt_valido(self, caminho):

        if not os.path.isfile(caminho):
            return False

        try:
            tamanho = os.path.getsize(caminho)

            if tamanho < 50:
                return False

            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read().strip()

            return len(conteudo) > 30

        except Exception as e:
            return False

    def iniciar(self):

        if hasattr(self, "processando") and self.processando:
            messagebox.showwarning(
                "Processando", "Já existe um vídeo em processamento."
            )
            return

        if not self.modelo_pronto:
            messagebox.showwarning("Atenção", "O modelo ainda não carregou.")
            return

        selecionados = []

        for v in self.videos:
            if not self.video_widgets[v]["checkbox"].get():
                continue

            nome = os.path.splitext(os.path.basename(v))[0]
            pasta_saida = os.path.join(os.path.dirname(v), nome)
            arquivo_txt = os.path.join(pasta_saida, nome + ".txt")

            if os.path.isfile(arquivo_txt):

                if self.txt_valido(arquivo_txt):
                    self.video_widgets[v]["status"].config(
                        text="Já processado", fg="yellow"
                    )
                    continue

            selecionados.append(v)
            self.video_widgets[v]["status"].config(text="Na fila", fg="white")

        if not selecionados:
            messagebox.showwarning(
                "Aviso", "Todos os vídeos selecionados já foram processados."
            )
            return

        self.processando = True
        self.cancelar = False
        self.inicio_global = time.time()

        self.btn_iniciar.config(state="disabled")
        self.btn_cancelar.config(bg="red", fg="white")

        for video in selecionados:
            self.executor.submit(self.processar_video_em_partes, video)

    def cancelar_processamento(self):
        self.cancelar = True
        self.processando = False

        for video, w in self.video_widgets.items():

            # 🔥 DESMARCA CHECKBOX
            w["checkbox"].set(False)

            if w["status"].cget("text") in ["Processando", "Aguardando", "Na fila"]:
                w["status"].config(text="Cancelado", fg="red")
                w["progress"]["value"] = 0
                w["percent"].config(text="0%")

                self.root.after(
                    5000,
                    lambda w=w: w["status"].config(text="Aguardando", fg="gray"),
                )

        # 🔥 LIMPA UI
        self.transcricao.config(state="normal")
        self.transcricao.delete("1.0", tk.END)
        self.transcricao.config(state="disabled")

        self.info_video_text.config(state="normal")
        self.info_video_text.delete("1.0", tk.END)
        self.info_video_text.config(state="disabled")

        self.label_tempo.config(text="Cancelado")

        self.btn_iniciar.config(state="normal")
        self.btn_cancelar.config(bg="#444")

    # =========================
    # PROCESSAMENTO EM PARTES
    # =========================
    def append_transcricao(self, texto):
        self.transcricao.config(state="normal")
        self.transcricao.insert(tk.END, texto + "\n")
        self.transcricao.see(tk.END)
        self.transcricao.config(state="disabled")

    def atualizar_painel(self):
        self.info_video_text.config(state="normal")
        self.info_video_text.delete("1.0", tk.END)

        d = self.detalhes

        texto = f"""
            🎬 STATUS
            ────────────────────────
            Estado: {d.get("status", "-")}

            🎞️ VÍDEO
            ────────────────────────
            Duração: {d.get("duracao", "-")}
            FPS: {d.get("fps", "-")}
            Resolução: {d.get("resolucao", "-")}

            🎧 ÁUDIO
            ────────────────────────
            Codec: {d.get("audio_codec", "-")}
            Sample Rate: {d.get("sample_rate", "-")}

            ⚙️ PROCESSAMENTO
            ────────────────────────
            Parte: {d.get("parte", "-")}
            Tempo extração: {d.get("extracao", "-")}
            Tempo transcrição: {d.get("transcricao", "-")}
            Tempo total vídeo: {d.get("tempo_parte", "-")}
            """

        self.info_video_text.insert(tk.END, texto)
        self.info_video_text.config(state="disabled")

    def processar_video_em_partes(self, video, duracao_parte=5):
        widget = self.video_widgets[video]
        barra = widget["progress"]
        status_label = widget["status"]
        percent_label = widget["percent"]

        if self.cancelar:
            return

        self.video_atual = video

        # =========================
        # 🎬 INICIALIZA PAINEL
        # =========================
        self.detalhes = {
            "status": "Iniciando...",
            "nome": os.path.basename(video),
            "caminho": video,
            "tamanho": f"{os.path.getsize(video)/(1024*1024):.2f}",
            "parte": "-",
            "extracao": "0s",
            "transcricao": "0s",
            "tempo_parte": "0s",
        }
        self.root.after(0, self.atualizar_painel)

        self.root.after(
            0, lambda: status_label.config(text="Processando", fg="#00ff88")
        )
        self.root.after(0, lambda: self.transcricao.delete("1.0", tk.END))
        self.root.after(0, lambda: self.info_video_text.delete("1.0", tk.END))

        # =========================
        # 📊 METADATA
        # =========================
        try:
            meta = ffmpeg.probe(video)

            video_stream = next(
                (s for s in meta["streams"] if s["codec_type"] == "video"), None
            )
            audio_stream = next(
                (s for s in meta["streams"] if s["codec_type"] == "audio"), None
            )

            duracao = float(meta["format"]["duration"])

            fps = eval(video_stream["r_frame_rate"]) if video_stream else 0
            resolucao = (
                f"{video_stream['width']}x{video_stream['height']}"
                if video_stream
                else "?"
            )

            self.detalhes.update(
                {
                    "status": "Metadata carregada",
                    "duracao": f"{int(duracao)}s",
                    "fps": f"{fps:.2f}",
                    "resolucao": resolucao,
                    "audio_codec": (
                        audio_stream.get("codec_name") if audio_stream else "?"
                    ),
                    "sample_rate": (
                        audio_stream.get("sample_rate") if audio_stream else "?"
                    ),
                }
            )

            self.root.after(0, self.atualizar_painel)

        except Exception as e:
            self.detalhes["status"] = f"Erro metadata: {e}"
            self.root.after(0, self.atualizar_painel)
            return

        # =========================
        # 📦 PARTES
        # =========================
        partes = list(range(0, int(duracao), duracao_parte))
        total_partes = len(partes)

        texto_completo = ""
        info = None

        # 🔥 ACUMULADORES
        total_extracao = 0
        total_transcricao = 0
        inicio_video = time.time()

        # =========================
        # 🔄 LOOP
        # =========================
        for i, inicio in enumerate(partes):

            if self.cancelar:
                self.root.after(
                    0, lambda: status_label.config(text="Cancelado", fg="red")
                )
                self.detalhes["status"] = "Cancelado"
                self.root.after(0, self.atualizar_painel)
                return

            inicio_parte = time.time()
            fim = min(inicio + duracao_parte, duracao)

            # Atualiza painel (parte atual)
            self.detalhes.update(
                {"status": "Processando...", "parte": f"{i+1}/{total_partes}"}
            )
            self.root.after(0, self.atualizar_painel)

            arquivo_audio = f"temp_{inicio}.wav"

            # =========================
            # 🎧 EXTRAÇÃO
            # =========================
            t0 = time.time()
            try:
                (
                    ffmpeg.input(video, ss=inicio, t=(fim - inicio))
                    .output(arquivo_audio, ac=1, ar=16000)
                    .overwrite_output()
                    .run(quiet=True)
                )
            except Exception as e:
                self.detalhes["status"] = f"Erro ffmpeg: {e}"
                self.root.after(0, self.atualizar_painel)
                continue

            t_extracao = time.time() - t0
            total_extracao += t_extracao

            # =========================
            # 🧠 TRANSCRIÇÃO
            # =========================
            t1 = time.time()
            try:
                segmentos, info = self.model.transcribe(
                    arquivo_audio,
                    beam_size=5,          # 🔥 melhora MUITO precisão
                    best_of=5,            # 🔥 escolhe melhor hipótese
                    temperature=0,        # mantém estável
                    vad_filter=True,
                    word_timestamps=False
                )
            except Exception as e:
                self.detalhes["status"] = f"Erro Whisper: {e}"
                self.root.after(0, self.atualizar_painel)
                os.remove(arquivo_audio)
                continue

            t_transcricao = time.time() - t1
            total_transcricao += t_transcricao

            # =========================
            # 📝 TEXTO
            # =========================
            buffer_ui = []

            for seg in segmentos:
                texto = seg.text.strip()
                linha = f"[{int(seg.start)}s] {texto}"

                texto_completo += linha + "\n"
                buffer_ui.append(linha)

            if self.video_atual == video and buffer_ui:
                bloco = "\n".join(buffer_ui)
                self.root.after(0, lambda t=bloco: self.append_transcricao(t))

            # =========================
            # 📊 PROGRESSO
            # =========================
            progresso = (i + 1) / total_partes
            porcentagem = int(progresso * 100)

            self.root.after(0, lambda: barra.config(value=porcentagem))
            self.root.after(0, lambda: percent_label.config(text=f"{porcentagem}%"))

            # =========================
            # ⏱ TEMPOS CLAROS
            # =========================
            tempo_parte = time.time() - inicio_parte
            tempo_total = time.time() - inicio_video

            self.detalhes.update(
                {
                    "extracao": f"{total_extracao:.2f}s (total)",
                    "transcricao": f"{total_transcricao:.2f}s (total)",
                    "tempo_parte": f"{tempo_total:.2f}s (total vídeo)",
                }
            )

            self.root.after(0, self.atualizar_painel)

            os.remove(arquivo_audio)

        # =========================
        # ✅ FINAL
        # =========================
        self.root.after(
            0, lambda: status_label.config(text="Concluído ✔", fg="#00ff88")
        )
        self.root.after(0, lambda: barra.config(value=100))
        self.root.after(0, lambda: percent_label.config(text="100%"))

        idioma = getattr(info, "language", "desconhecido") if info else "desconhecido"

        self.salvar_saida(video, texto_completo, idioma)

        self.detalhes["status"] = "Concluído ✔"
        self.root.after(0, self.atualizar_painel)

        self.processando = False
        self.root.after(0, lambda: self.btn_iniciar.config(state="normal"))

    # =========================
    def salvar_saida(self, video, texto, idioma):
        nome = os.path.splitext(os.path.basename(video))[0]
        pasta_saida = os.path.join(os.path.dirname(video), nome)
        os.makedirs(pasta_saida, exist_ok=True)
        with open(os.path.join(pasta_saida, nome + ".txt"), "w", encoding="utf-8") as f:
            f.write(texto)
        self.gerar_pdf(
            os.path.join(pasta_saida, nome + "_relatorio.pdf"), video, idioma
        )

    def gerar_pdf(self, caminho, video, idioma):
        doc = SimpleDocTemplate(caminho, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("RELATÓRIO DE TRANSCRIÇÃO", styles["Heading1"]))
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(f"Arquivo: {video}", styles["Normal"]))
        elements.append(Paragraph(f"Idioma: {idioma}", styles["Normal"]))
        elements.append(Paragraph(f"Data: {datetime.now()}", styles["Normal"]))
        doc.build(elements)

    def atualizar_eta(self):
        tempo_passado = time.time() - self.inicio_global
        self.label_eta.config(text=f"Tempo decorrido: {int(tempo_passado)} segundos")


# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = TranscritorPro(root)
    root.mainloop()
