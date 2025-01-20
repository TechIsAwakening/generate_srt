# Generate SRT Subtitles

Ce script Python génère automatiquement des sous-titres au format SRT à partir de fichiers vidéo MP4. Il utilise les modèles de transcription Whisper et l'API OpenAI pour fournir des transcriptions et des traductions précises.

---

## 📋 **Fonctionnalités**
- Extraction de l'audio des vidéos MP4.
- Découpage de l'audio en segments pour traiter de longues vidéos.
- Transcription avec Whisper.
- Traduction du texte transcrit dans la langue cible grâce à OpenAI.
- Génération de fichiers SRT contenant les sous-titres avec timestamps.

---

## 🛠️ **Prérequis**
### Bibliothèques Python nécessaires :
- `whisper`
- `openai`
- `os`
- `subprocess`
- `math`
- `argparse`

### Installation des dépendances :
```bash
pip install whisper openai
```

### Outils externes :
- **FFmpeg** : pour extraire et découper l'audio. [Téléchargez FFmpeg](https://ffmpeg.org/download.html).

---

## ⚙️ **Configuration**
1. Ajoutez votre clé API OpenAI dans le fichier :
   ```python
   OPENAI_API_KEY = "votre-clé-API"
   ```
2. Définissez les paramètres globaux (optionnels) :
   - `CHUNK_DURATION` : Durée maximale en secondes d'un segment audio (par défaut : 900 secondes).
   - `WHISPER_MODEL` : Modèle Whisper à utiliser (`medium`, `large`, etc.).
   - `DEFAULT_TARGET_LANG` : Langue cible par défaut pour la traduction (par exemple : `'fr'` pour le français).

---

## ▶️ **Utilisation**
### Ligne de commande :
1. Placez vos fichiers vidéo MP4 dans le même dossier que le script.
2. Exécutez la commande suivante :
   ```bash
   python generate_srt.py
   ```
   - `--target-lang` : Langue cible pour la traduction (`espagnol`, `italien`, etc.).
   - `--chunk-duration` : Durée maximale d'un segment audio (en secondes).

### Exemple :
```bash
python generate_srt.py --target-lang fr
```
Cela génère un fichier SRT pour chaque vidéo MP4 du dossier.

---

## 🚯 **Nettoyage**
Les fichiers audio temporaires générés par FFmpeg sont automatiquement supprimés après le traitement.

---

## 📄 **Structure du Code**
- **extract_audio** : Extrait la piste audio d'une vidéo MP4.
- **split_audio** : Divise l'audio en segments.
- **transcribe_with_whisper** : Transcrit un fichier audio en texte.
- **translate_text** : Traduit le texte transcrit dans la langue cible.
- **segments_to_srt** : Convertit les segments en format SRT.

---

## 🚀 **Améliorations Futures**
- Support pour d'autres formats vidéo.
- Ajout de paramètres configurables via un fichier externe.
- Optimisation pour des modèles Whisper plus grands.

---

## ❗ **Attention**
- Ne partagez pas votre clé API OpenAI publiquement.
- Vérifiez que les vidéos ne contiennent pas de données sensibles avant de partager les sous-titres.

---

## 🖋️ **Licence**
Ce script est fourni "tel quel". Vous pouvez l'utiliser et le modifier librement pour des projets personnels ou professionnels.
