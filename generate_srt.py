#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import math
import whisper
import openai
import warnings

# -------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------
# Taille d'un segment audio (en secondes) si on veut découper
# (par exemple, 15 minutes = 900 secondes)
CHUNK_DURATION = 900

# Modèle Whisper à charger (medium, large, etc.)
WHISPER_MODEL = "medium"

# Langue cible par défaut
DEFAULT_TARGET_LANG = "en"

# Clé API OpenAI
OPENAI_API_KEY = "ENTREZ ICI VOTRE CLEE OPEN AI"
openai.api_key = OPENAI_API_KEY

# Désactiver les warnings
warnings.filterwarnings("ignore", category=UserWarning)

# -------------------------------------------------------------------------
# FONCTIONS UTILITAIRES
# -------------------------------------------------------------------------
def extract_audio(input_video_path, output_audio_path):
    """
    Extrait la piste audio d'une vidéo mp4 en .mp3 (16kHz, compressé) via ffmpeg.
    """
    cmd = [
        "ffmpeg",
        "-y",                 # écrase le fichier s'il existe
        "-i", input_video_path,
        "-vn",                # pas de flux vidéo
        "-acodec", "libmp3lame",  # codec audio MP3
        "-b:a", "160k",       # débit binaire à 160 kbps (bonne qualité)
        "-ar", "16000",       # échantillonnage 16kHz (optimisé pour Whisper)
        "-ac", "1",           # audio mono
        output_audio_path
    ]
    subprocess.run(cmd, check=True)


def split_audio(input_audio_path, chunk_duration=CHUNK_DURATION):
    """
    Découpe un fichier audio en plusieurs segments de 'chunk_duration' secondes.
    Retourne la liste des chemins des segments générés.
    """
    # On récupère la durée totale du fichier audio, via ffprobe
    cmd_duration = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_audio_path
    ]
    total_duration_str = subprocess.check_output(cmd_duration).decode().strip()
    total_duration = float(total_duration_str)

    # Calcul du nombre de chunks à générer
    nb_chunks = math.ceil(total_duration / chunk_duration)

    # Liste des chemins d'audio découpés
    chunk_paths = []

    for i in range(nb_chunks):
        start_time = i * chunk_duration
        output_file = f"{input_audio_path}.{i}.mp3"
        cmd_split = [
            "ffmpeg",
            "-y",
            "-i", input_audio_path,
            "-ss", str(start_time),                # début du segment
            "-t", str(chunk_duration),             # durée du segment
            "-acodec", "copy",                     # copie sans ré-encoder
            output_file
        ]
        subprocess.run(cmd_split, check=True)
        chunk_paths.append(output_file)

    return chunk_paths


def transcribe_with_whisper(audio_path, source_lang="auto", model_size=WHISPER_MODEL):
    """
    Transcrit un fichier audio en utilisant Whisper.
    Retourne un dictionnaire contenant des segments avec timestamps et textes.
    """
    model = whisper.load_model(model_size)

    # Transcription
    result = model.transcribe(
        audio_path,
        task="transcribe",
        language=None if source_lang == "auto" else source_lang
    )

    return result


def translate_text(text, target_lang):
    """
    Traduit un texte donné en utilisant l'API OpenAI vers la langue cible.
    """
    prompt = (
        f"Traduisez le texte suivant en {target_lang} :\n\n{text}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content'].strip()


def segments_to_srt(segments, offset=0.0, target_lang=None):
    """
    Convertit la liste de segments renvoyés par Whisper en texte SRT.
    offset : décalage à appliquer sur les timestamps (en secondes) pour recaler
             les segments quand on fait du chunking.
    target_lang : si défini, traduit le texte en utilisant OpenAI.
    """
    srt_content = []
    for i, seg in enumerate(segments):
        # Index du sous-titre
        srt_content.append(str(i+1))

        # Timestamps
        start = seg["start"] + offset
        end = seg["end"] + offset

        # Format SRT HH:MM:SS,millisecondes
        start_srt = format_srt_timestamp(start)
        end_srt = format_srt_timestamp(end)
        srt_content.append(f"{start_srt} --> {end_srt}")

        # Texte
        srt_text = seg["text"].strip()
        if target_lang and target_lang != "en":
            srt_text = translate_text(srt_text, target_lang)
        srt_content.append(srt_text)
        srt_content.append("")  # ligne vide après chaque sous-titre

    return "\n".join(srt_content)


def format_srt_timestamp(seconds):
    """
    Convertit des secondes float en timestamp SRT (HH:MM:SS,mmm).
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# -------------------------------------------------------------------------
# FONCTION PRINCIPALE
# -------------------------------------------------------------------------
def generate_srt(
    input_video_path,
    source_lang="auto",
    target_lang=DEFAULT_TARGET_LANG,
    chunk_duration=CHUNK_DURATION
):
    """
    Génère un fichier SRT transcrit/traduit à partir d'une vidéo MP4.
    - input_video_path : chemin de la vidéo
    - source_lang      : langue source (e.g., 'en', 'fr', ou 'auto')
    - target_lang      : langue de traduction (e.g., 'fr', 'es') ou None si pas de trad
    - chunk_duration   : taille de découpage (en s) pour l'audio
    """
    video_name = os.path.splitext(os.path.basename(input_video_path))[0]
    output_srt_path = f"{video_name}.srt"

    # 1. Extraire l'audio en mp3
    audio_path = "temp_audio.mp3"
    extract_audio(input_video_path, audio_path)

    # 2. Découper l'audio en chunks si besoin
    chunk_paths = split_audio(audio_path, chunk_duration=chunk_duration)

    # 3. Pour chaque chunk, on transcrit et traduit
    full_segments = []
    offset = 0.0

    for idx, chunk_path in enumerate(chunk_paths):
        # Récupérer la durée du chunk pour mettre à jour l'offset
        cmd_chunk_dur = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            chunk_path
        ]
        chunk_duration_str = subprocess.check_output(cmd_chunk_dur).decode().strip()
        chunk_len = float(chunk_duration_str)

        # Transcription
        print(f"[INFO] Transcription du chunk {idx+1}/{len(chunk_paths)}...")
        result = transcribe_with_whisper(chunk_path, source_lang)

        # Ajuster chaque segment avec l'offset
        for seg in result["segments"]:
            seg["start"] += offset
            seg["end"] += offset

            # Traduire le texte si la langue cible n'est pas l'anglais
            if target_lang != "en":
                seg["text"] = translate_text(seg["text"], target_lang)

            full_segments.append(seg)

        offset += chunk_len

    # 4. Convertir tous les segments en texte SRT avec traduction
    srt_data = segments_to_srt(full_segments, offset=0.0, target_lang=None)

    # 5. Sauvegarder le fichier .srt
    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write(srt_data)

    # Nettoyage
    if os.path.exists(audio_path):
        os.remove(audio_path)

    for cp in chunk_paths:
        if os.path.exists(cp):
            os.remove(cp)

    print(f"[DONE] Fichier SRT généré : {output_srt_path}")


# -------------------------------------------------------------------------
# MAIN (exemple d'utilisation)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Générer des sous-titres SRT pour toutes les vidéos dans un dossier.")
    parser.add_argument("--target-lang", default=DEFAULT_TARGET_LANG, help="Langue cible (ex: 'en', 'fr', 'es') (défaut: en)")
    parser.add_argument("--chunk-duration", type=int, default=900, help="Durée max (en secondes) pour diviser l'audio (défaut: 900s = 15min)")

    # Utiliser le dossier contenant ce script comme chemin par défaut
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = script_dir

    # Lister toutes les vidéos dans le dossier
    video_files = [
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.lower().endswith(".mp4")
    ]

    for video_path in video_files:
        print(f"[INFO] Traitement de la vidéo : {video_path}")
        generate_srt(
            input_video_path=video_path,
            source_lang="auto",
            target_lang=parser.parse_args().target_lang,
            chunk_duration=parser.parse_args().chunk_duration
        )
