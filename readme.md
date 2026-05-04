# 🎬 TranscritorPro — Sistema de Transcrição de Vídeos


>
> ![preview](https://transcri.io/img/visual/audio-transcription.svg)
>
---

## 📌 Sobre o Projeto

O **TranscritorPro** é uma aplicação desktop desenvolvida em Python com interface gráfica (Tkinter) para transcrição de vídeos e áudios.

O sistema utiliza processamento local com extração de áudio via FFmpeg e transcrição com modelo embarcado, sem depender de APIs externas.

---

## 🚀 Funcionalidades

✔ Seleção de pasta com vídeos/áudios
✔ Processamento por partes (mais estabilidade)
✔ Exibição de progresso em tempo real
✔ Interface em modo escuro
✔ Cancelamento de processamento
✔ Geração de arquivos `.txt` e `.pdf`

---

## ⚙️ Tecnologias Utilizadas

* Python 3
* Tkinter
* FFmpeg (extração de áudio)
* Torch (execução local)
* Faster-Whisper (processamento local)
* ReportLab (PDF)

---

## 📦 Instalação (SEM VENV)

### 1. Instalar Python

Baixe:
👉 https://www.python.org/downloads/

---

## 🎧 2. Instalar FFmpeg (OBRIGATÓRIO)

### Passo a passo (Windows)

1. Baixe o FFmpeg:

👉 https://www.gyan.dev/ffmpeg/builds/

Baixe a versão:

* **release full build**

---

2. Extraia o arquivo `.zip`

Exemplo:

```bash
C:\ffmpeg
```

A estrutura deve ficar assim:

```bash
C:\ffmpeg\bin\ffmpeg.exe
```

---

3. Adicionar ao PATH

### Passos:

1. Pressione `Win + S`
2. Pesquise: **Variáveis de Ambiente**
3. Clique em: **Editar variáveis de ambiente do sistema**
4. Clique em **Variáveis de Ambiente**
5. Em **Path** → clique em **Editar**
6. Clique em **Novo**
7. Adicione:

```bash
C:\ffmpeg\bin
```

8. Clique em OK em tudo

---

4. Testar instalação

Abra o terminal e rode:

```bash
ffmpeg -version
```

Se aparecer informações do FFmpeg, está OK ✅

---

## 📦 3. Instalar dependências Python

```bash
pip install torch faster-whisper reportlab ffmpeg-python
```

---

## ▶️ Como Executar

```bash
python nome_do_arquivo.py
```

---

## ⚡ Processamento (IMPORTANTE)

O sistema utiliza **processamento bruto local**.

### 🔹 CPU

✔ Funciona em qualquer máquina
✔ Usa múltiplos núcleos (dependendo do modelo)

---

### 🔹 GPU NVIDIA (CUDA)

Se houver GPU NVIDIA compatível:

✔ Pode acelerar o processamento
✔ Detectado automaticamente pelo sistema

---

### ⚠️ AMD (RX 7600, Ryzen, etc.)

❌ Não suporta CUDA
✔ O sistema roda **somente via CPU**

---

### 🔧 Forçar CPU (opcional)

```python
DEVICE = "cpu"
COMPUTE_TYPE = "int8"
```

---

## 📊 Performance

Depende de:

* Processador (Ryzen 7 / Ryzen 9 → ótimo)
* Tamanho do modelo
* Tamanho do vídeo

---

## 📁 Saída dos Arquivos

Para cada vídeo:

```bash
/video_nome/
 ├── video_nome.txt
 └── video_nome_relatorio.pdf
```

---

## 🧪 Fluxo de Uso

1. Clique em **Selecionar Pasta**
2. Marque os arquivos
3. Clique em **Iniciar**
4. Acompanhe o progresso
5. Resultado salvo automaticamente

---

## ❌ Cancelamento

Ao cancelar:

* Processamento interrompido
* Checkboxes desmarcados
* Interface limpa

---

## 🧼 Comportamento

✔ Limpa transcrição ao trocar vídeo
✔ Evita reprocessar arquivos já feitos
✔ Processamento por partes (mais estável)

---

## 🛠️ Problemas Comuns

### ❌ FFmpeg não funciona

✔ Verifique se está em:

```bash
C:\ffmpeg\bin
```

✔ Verifique PATH corretamente

---

### ❌ Lento

✔ Use modelo menor
✔ CPU é o principal fator

---

## 📌 Configuração recomendada

```python
MODEL_SIZE = "medium"
```

---

## 👨‍💻 Observação Final

Este sistema roda totalmente local, sem dependência de serviços externos, utilizando processamento direto da máquina.

---

## 📄 Licença

Uso livre para estudos e projetos pessoais.

---
