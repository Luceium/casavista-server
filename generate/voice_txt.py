def get_transcript(voice):
    file_path = voice.get("filePath")
    logger.info(f"File path received: {file_path}")
    
    # Validate input
    if not file_path:
        logger.error("error: File path is missing")
        return jsonify({"error": "File path is missing"}), 400

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
            logger.error("error: Failed download is missing")
            return jsonify({"error": f"Failed to download file: {str(e)}"}), 400
    else:
        temp_file_path = file_path

    # Validate file exists
    if not os.path.exists(temp_file_path):
        logger.error("file not found")
        return jsonify({"error": f"File not found: {temp_file_path}"}), 400

    try:
        # Transcribe file
        result = transcribe_with_faster_whisper(file_path=temp_file_path, compute_type="default")
        
        # Ensure the result is properly returned in the response
        return jsonify({"message": "Transcription successful", "data": result}), 200
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
    finally:
        if file_path.startswith("http://") or file_path.startswith("https://"):
            os.remove(temp_file_path)

import tempfile
import boto3
import time
import requests
from common.utils import safe_get_env_var
from pydub import AudioSegment
from pydub.utils import make_chunks
import os
from faster_whisper import WhisperModel
import torch
# import whisper as local_whisper

device = "cuda" if torch.cuda.is_available() else "cpu"

openai_key = safe_get_env_var('OPENAI_API_KEY')

s3_client = boto3.client('s3')
ssm_client = boto3.client('ssm',  region_name='us-east-1')
transcribe_client = boto3.client('transcribe', region_name='us-east-2')

def load_counter(parameter_name: str = "TranscriptionJobCounter"):
    global count
    try:
        response = ssm_client.get_parameter(Name=parameter_name)
        count = int(response['Parameter']['Value'])
    except:
        count = 0

def transcribe_with_aws(file_path: str, bucket_name: str = "david-signaccess-test", 
                        job_base_name: str = "TranscriptionJob", parameter_name: str = "TranscriptionJobCounter"):
    """
    Transcribes an audio or video file on AWS using AWS Transcribe. First uploads the file to an S3 bucket and requires AWS CLI to be configured with `aws configure` in terminal.

    Args:
        file_path (str): Path to the audio or video file.
        bucket_name (str): Bucket to store file in.
        job_base_name (str): Base name to be concatenated with counter for AWS Transcribe jobs.
        parameter_name (str): Name for counter. (should be consistent for all AWS Transcribe calls)

    Returns:
        A dictionary containing the string transcription and a list of words. (each with a timestamp and if it is a punctuation or not)

    Raises:
        Exception: If any error occurs during transcription.
    """
    global count
    try:
        job_name = f"{job_base_name}_{count}"
        video_name = f"video_{count}.mp4"
        s3_client.upload_file(Filename=file_path, Bucket=bucket_name, Key=video_name)

        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f"s3://{bucket_name}/{video_name}"},
            MediaFormat='mp4',
            LanguageCode='en-US'
        )

        while True:
            job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)['TranscriptionJob']
            status = job['TranscriptionJobStatus']

            if status == 'FAILED':
                break

            if status == 'COMPLETED':
                transcript_uri = job['Transcript']['TranscriptFileUri']
                transcript_json = requests.get(transcript_uri).json()
                transcript = transcript_json['results']['transcripts'][0]['transcript']
                words = transcript_json['results']['items']
                break

            time.sleep(0.25)

        count += 1
        ssm_client.put_parameter(
            Name=parameter_name,
            Value=str(count),
            Type="String",
            Overwrite=True
        )
        return {'transcript': transcript, 'words': words}
    except Exception as e:
        return e

def split_audio(file_path: str, chunk_size_mb: int = 25):
    """
    Splits an audio file into smaller chunks.

    Args:
        file_path (str): Path to the input audio file.
        chunk_size_mb (int): Maximum chunk size in megabytes.

    Returns:
        list: Paths to the smaller audio chunks.
    """
    audio = AudioSegment.from_file(file_path)
    chunk_size_bytes = chunk_size_mb * 1024 * 1024  # Convert MB to bytes
    chunk_length_ms = len(audio) * chunk_size_bytes // os.path.getsize(file_path)
    chunks = make_chunks(audio, chunk_length_ms)
    
    chunk_paths = []
    for i, chunk in enumerate(chunks):
        chunk_path = f"{file_path}_chunk{i}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunk_paths.append(chunk_path)
    return chunk_paths

# def transcribe_with_local_whisper(file_path: str, model_size: str = "base") -> dict:
#     """
#     Transcribes an audio file using OpenAI's Whisper model locally.

#     Args:
#         file_path (str): Path to the audio file.
#         model_size (str): Model size to use (e.g., "tiny", "base", "small", "medium", "large").

#     Returns:
#         dict: A dictionary containing the transcript and segment data.

#     Raises:
#         Exception: If any error occurs during transcription.
#     """
#     try:
#         # Load the Whisper model
#         model = local_whisper.whisper.load_model(model_size)

#         # Transcribe the audio file
#         result = model.transcribe(file_path)

#         # Extract the transcript and segments
#         transcript = result.get("text", "")
#         segments = result.get("segments", [])

#         return {
#             "transcript": transcript,
#             "segments": segments
#         }
#     except Exception as e:
#         # logger.error(f"Error in transcribe_with_local_whisper: {str(e)}", exc_info=True)
#         raise e
import subprocess

def extract_audio(input_file):
    audio_path = input_file.replace(".mp4", ".wav")

    # Check if the input file contains audio stream
    command = ['ffmpeg', '-i', input_file]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "Audio" not in result.stderr:
            raise ValueError("No audio stream found in the input file.")
        
        # Proceed with the extraction if audio exists
        command = [
            'ffmpeg', '-i', input_file, 
            '-vn', '-acodec', 'pcm_s16le', 
            '-ar', '44100', '-ac', '2', 
            audio_path
        ]
        subprocess.run(command, check=True)
        print(f"Audio extracted successfully to {audio_path}")
        return audio_path
    except subprocess.CalledProcessError as e:
        print(f"Error executing ffmpeg: {e.stderr}")
    except ValueError as ve:
        print(ve)

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
    segment_list = [{"start": segment.start, "end": segment.end, "text": segment.text} for segment in segments]
    return segment_list


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