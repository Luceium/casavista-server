import tempfile
import time
import requests
from pydub import AudioSegment
from pydub.utils import make_chunks
import os
from faster_whisper import WhisperModel
import torch
from fastapi.responses import JSONResponse

def get_transcript(file_path):
    print("start transcribing")
    print(f"File path received: {file_path}")
    
    # Validate input
    if not file_path:
        print("error: File path is missing")
        return JSONResponse(content={"error": "File path is missing"}), 400

    # Handle URL or local file
    if file_path.startswith("http://") or file_path.startswith("https://"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1]) as temp_file:
                response = requests.get(file_path, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
        except Exception as e:
            print("error: Failed download is missing")
            return JSONResponse({"error": f"Failed to download file: {str(e)}"}), 400
    else:
        temp_file_path = file_path

    # Validate file exists
    if not os.path.exists(temp_file_path):
        print("file not found")
        return JSONResponse({"error": f"File not found: {temp_file_path}"}), 400

    try:
        # Transcribe file
        result = transcribe_with_faster_whisper(file_path=temp_file_path, compute_type="default")
        
        # Ensure the result is properly returned in the response
        return result
    except Exception as e:
        return JSONResponse({"error": f"Transcription failed: {str(e)}"}), 500
    finally:
        if file_path.startswith("http://") or file_path.startswith("https://"):
            os.remove(temp_file_path)

device = "cuda" if torch.cuda.is_available() else "cpu"

import subprocess


def transcribe_with_faster_whisper(file_path: str, model_size: str = "base", compute_type="float16"):
    """
    Transcribes an audio or video file locally using an optimized version OpenAI's Whisper model with CTranslate2.

    Args:
        file_path (str): Path to the audio or video file.
        model_size (str): Model size to use (e.g., "tiny", "base", "small", "medium", "large").

    Returns:
        A list containing the segments, each with text, start, and end attributes.

    Raises:
        Exception: If any error occurs during transcription.
    """
    # Check if file is MP4, and extract audio if so
    if file_path.endswith(".mp4"):
        audio_path = extract_audio(file_path)
        file_path = audio_path

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    segments, _ = model.transcribe(file_path, beam_size=5)
    # segment_list = [{"start": segment.start, "end": segment.end, "text": segment.text} for segment in segments]
    segments = [segment.text for segment in segments]
    print(segments)
    text = segments[0] if len(segments) == 1 else " ".join([segment.text for segment in segments])
    print("Got transcript: ", text)
    return text


def faster_whisper_transcriber(file_path):

    # Handle URL or local file
    if file_path.startswith("http://") or file_path.startswith("https://"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1]) as temp_file:
                response = requests.get(file_path, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
        except Exception as e:
            raise RuntimeError(f"Failed to download file: {str(e)}") from e
    else:
        temp_file_path = file_path

    # Validate file exists
    if not os.path.exists(temp_file_path):
        raise RuntimeError(f"File not found: {str(temp_file_path)}")

    try:
        # Transcribe file
        result = transcribe_with_faster_whisper(file_path=temp_file_path, compute_type="default")
        return result
    except Exception as e:
        raise RuntimeError(f"transcription failed: {str(e)}") from e
    finally:
        if file_path.startswith("http://") or file_path.startswith("https://"):
            os.remove(temp_file_path)