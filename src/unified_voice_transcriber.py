#!/usr/bin/env python3
"""
Unified Voice Transcriber - Multi-language support with speaker diarization
Handles English, Hindi, Hinglish, and other languages automatically
"""

import os
import sys
import argparse
import whisper
from pydub import AudioSegment
from pydub.silence import split_on_silence
import markdown
from datetime import datetime
import json
from pathlib import Path
from tqdm import tqdm
import logging
import numpy as np
import torch
import torchaudio
import librosa
from scipy.spatial.distance import cdist
from sklearn.cluster import AgglomerativeClustering
import warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedVoiceTranscriber:
    def __init__(self, model_size="base", enable_speaker_diarization=True):
        """
        Initialize the unified voice transcriber
        
        Args:
            model_size (str): Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            enable_speaker_diarization (bool): Whether to enable speaker identification
        """
        self.model_size = model_size
        self.model = None
        self.enable_speaker_diarization = enable_speaker_diarization
        self.supported_formats = ['.mp3', '.m4a', '.wav', '.aac', '.flac', '.ogg', '.wma']
        
        # Multi-language settings
        self.language = None  # Will be auto-detected
        self.task = "transcribe"
        
        # Speaker diarization settings
        self.speaker_settings = {
            "min_speakers": 1,
            "max_speakers": 10,
            "silence_threshold": 0.5,
            "min_speech_duration": 0.5,
            "min_silence_duration": 0.3
        }
        
        # Language-specific settings
        self.language_configs = {
            "en": {"name": "English", "bilingual": False},
            "hi": {"name": "Hindi", "bilingual": True},
            "auto": {"name": "Auto-detected", "bilingual": True}
        }
        
    def load_model(self):
        """Load the Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def convert_audio_format(self, input_path, output_format="wav"):
        """
        Convert audio to a supported format for Whisper
        
        Args:
            input_path (str): Path to input audio file
            output_format (str): Desired output format
            
        Returns:
            str: Path to converted audio file
        """
        try:
            audio = AudioSegment.from_file(input_path)
            output_path = input_path.rsplit('.', 1)[0] + f".{output_format}"
            audio.export(output_path, format=output_format)
            logger.info(f"Converted {input_path} to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            raise
    
    def extract_audio_features(self, audio_path):
        """
        Extract audio features for speaker diarization
        
        Args:
            audio_path (str): Path to audio file
            
        Returns:
            tuple: (features, sample_rate, duration)
        """
        try:
            # Load audio with librosa
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Extract spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            # Combine features
            features = np.vstack([mfcc, spectral_centroids, spectral_rolloff])
            
            duration = len(y) / sr
            
            return features, sr, duration
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            raise
    
    def perform_speaker_diarization(self, audio_path):
        """
        Perform speaker diarization using audio features
        
        Args:
            audio_path (str): Path to audio file
            
        Returns:
            list: List of speaker segments with timestamps
        """
        try:
            logger.info("Performing speaker diarization...")
            
            # Extract audio features
            features, sr, duration = self.extract_audio_features(audio_path)
            
            # Segment audio into chunks
            chunk_duration = 3.0  # 3-second chunks
            chunk_samples = int(chunk_duration * sr)
            
            segments = []
            for i in range(0, len(features[0]), chunk_samples):
                chunk_features = features[:, i:i+chunk_samples]
                if chunk_features.shape[1] > 0:
                    # Calculate mean features for the chunk
                    chunk_mean = np.mean(chunk_features, axis=1)
                    segments.append({
                        'start': i / sr,
                        'end': min((i + chunk_samples) / sr, duration),
                        'features': chunk_mean
                    })
            
            if len(segments) < 2:
                # Not enough segments for diarization
                return [{'start': 0, 'end': duration, 'speaker': 'Speaker 1'}]
            
            # Extract feature vectors for clustering
            feature_vectors = np.array([seg['features'] for seg in segments])
            
            # Determine optimal number of speakers (1-5)
            max_speakers = min(5, len(segments) // 2)
            best_n_clusters = 1
            best_score = float('inf')
            
            for n_clusters in range(1, max_speakers + 1):
                clustering = AgglomerativeClustering(n_clusters=n_clusters)
                labels = clustering.fit_predict(feature_vectors)
                
                # Calculate silhouette score (simplified)
                if n_clusters > 1:
                    # Calculate within-cluster variance
                    score = 0
                    for cluster_id in range(n_clusters):
                        cluster_points = feature_vectors[labels == cluster_id]
                        if len(cluster_points) > 1:
                            centroid = np.mean(cluster_points, axis=0)
                            score += np.mean(cdist(cluster_points, [centroid], 'euclidean'))
                    
                    if score < best_score:
                        best_score = score
                        best_n_clusters = n_clusters
            
            # Perform final clustering
            clustering = AgglomerativeClustering(n_clusters=best_n_clusters)
            labels = clustering.fit_predict(feature_vectors)
            
            # Assign speaker labels
            speaker_segments = []
            for i, seg in enumerate(segments):
                speaker_id = f"Speaker {labels[i] + 1}"
                speaker_segments.append({
                    'start': seg['start'],
                    'end': seg['end'],
                    'speaker': speaker_id
                })
            
            # Merge consecutive segments from same speaker
            merged_segments = []
            current_speaker = None
            current_start = 0
            
            for seg in speaker_segments:
                if current_speaker != seg['speaker']:
                    if current_speaker is not None:
                        merged_segments.append({
                            'start': current_start,
                            'end': seg['start'],
                            'speaker': current_speaker
                        })
                    current_speaker = seg['speaker']
                    current_start = seg['start']
            
            # Add final segment
            if current_speaker is not None:
                merged_segments.append({
                    'start': current_start,
                    'end': duration,
                    'speaker': current_speaker
                })
            
            logger.info(f"Speaker diarization completed. Found {best_n_clusters} speakers.")
            return merged_segments
            
        except Exception as e:
            logger.error(f"Error in speaker diarization: {e}")
            # Fallback to single speaker
            return [{'start': 0, 'end': duration, 'speaker': 'Speaker 1'}]
    
    def transcribe_audio(self, audio_path, output_dir=None, language="auto", 
                        temperature=0.2, beam_size=5, best_of=1, 
                        patience=1.0, length_penalty=1.0):
        """
        Transcribe audio file using Whisper with automatic language detection
        
        Args:
            audio_path (str): Path to audio file
            output_dir (str): Directory to save output files
            language (str): Language code or "auto" for auto-detection
            temperature (float): Sampling temperature (0.0 to 1.0)
            beam_size (int): Beam size for beam search
            best_of (int): Number of candidates to consider
            patience (float): Patience for early stopping
            length_penalty (float): Length penalty for beam search
            
        Returns:
            dict: Transcription results with speaker information
        """
        if not self.model:
            self.load_model()
        
        try:
            logger.info(f"Transcribing: {audio_path}")
            
            # Perform speaker diarization if enabled
            speaker_segments = []
            if self.enable_speaker_diarization:
                speaker_segments = self.perform_speaker_diarization(audio_path)
            
            # Transcribe the audio with supported parameters
            transcribe_kwargs = {
                'word_timestamps': True,
                'temperature': temperature
            }
            
            # Set language if specified
            if language != "auto":
                transcribe_kwargs['language'] = language
            else:
                transcribe_kwargs['language'] = None  # Auto-detect
            
            # Log unsupported parameters for user awareness
            unsupported_params = []
            if beam_size != 5:
                unsupported_params.append(f"beam_size={beam_size}")
            if best_of != 1:
                unsupported_params.append(f"best_of={best_of}")
            if patience != 1.0:
                unsupported_params.append(f"patience={patience}")
            if length_penalty != 1.0:
                unsupported_params.append(f"length_penalty={length_penalty}")
            
            if unsupported_params:
                logger.warning(f"Parameters not supported by current Whisper version: {', '.join(unsupported_params)}")
                logger.info("Using default values for unsupported parameters")
            
            result = self.model.transcribe(audio_path, **transcribe_kwargs)
            
            # Store detected language
            self.language = result.get("language", "unknown")
            logger.info(f"Detected language: {self.language}")
            
            # Process segments and add speaker information
            if "segments" in result and speaker_segments:
                result = self._align_speakers_with_segments(result, speaker_segments)
            
            logger.info("Transcription completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise
    
    def _align_speakers_with_segments(self, transcription_result, speaker_segments):
        """
        Align speaker information with transcription segments
        
        Args:
            transcription_result (dict): Whisper transcription result
            speaker_segments (list): Speaker diarization segments
            
        Returns:
            dict: Transcription result with speaker information
        """
        try:
            segments = transcription_result.get("segments", [])
            
            for segment in segments:
                segment_start = segment["start"]
                segment_end = segment["end"]
                
                # Find which speaker was active during this segment
                speaker = "Unknown Speaker"
                max_overlap = 0
                
                for spk_seg in speaker_segments:
                    spk_start = spk_seg["start"]
                    spk_end = spk_seg["end"]
                    
                    # Calculate overlap
                    overlap_start = max(segment_start, spk_start)
                    overlap_end = min(segment_end, spk_end)
                    overlap = max(0, overlap_end - overlap_start)
                    
                    if overlap > max_overlap:
                        max_overlap = overlap
                        speaker = spk_seg["speaker"]
                
                segment["speaker"] = speaker
                
                # Convert timestamps to readable format
                segment["start_formatted"] = self.format_timestamp(segment_start)
                segment["end_formatted"] = self.format_timestamp(segment_end)
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Error aligning speakers with segments: {e}")
            return transcription_result
    
    def format_timestamp(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def save_transcription_markdown(self, transcription, output_path, metadata=None):
        """
        Save transcription in markdown format with language-appropriate content
        
        Args:
            transcription (dict): Transcription results from Whisper
            output_path (str): Path to save markdown file
            metadata (dict): Additional metadata about the audio file
        """
        try:
            # Create markdown content based on detected language
            md_content = self._generate_markdown_content(transcription, metadata)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.info(f"Markdown saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving markdown: {e}")
            raise
    
    def _generate_markdown_content(self, transcription, metadata=None):
        """Generate markdown content based on detected language"""
        content = []
        
        # Get language info
        lang_code = self.language
        lang_config = self.language_configs.get(lang_code, self.language_configs["auto"])
        lang_name = lang_config["name"]
        is_bilingual = lang_config["bilingual"]
        
        # Header based on language
        if lang_code == "hi":
            content.append("# Voice Memo Transcription - हिंदी/हिंग्लिश\n")
            content.append("*वॉइस मेमो ट्रांसक्रिप्शन*\n")
        elif lang_code == "en":
            content.append("# Voice Memo Transcription - English\n")
        else:
            content.append(f"# Voice Memo Transcription - {lang_name}\n")
            if is_bilingual:
                content.append("*Multi-language transcription*\n")
        
        # Metadata
        if metadata:
            content.append("## File Information / फ़ाइल जानकारी\n")
            for key, value in metadata.items():
                content.append(f"- **{key}**: {value}")
            content.append("")
        
        # Transcription text
        content.append("## Transcription / ट्रांसक्रिप्शन\n")
        content.append(f"{transcription['text']}\n")
        
        # Segments with speakers and timestamps
        if "segments" in transcription and transcription["segments"]:
            content.append("## Detailed Segments / विस्तृत सेगमेंट्स\n")
            
            # Table headers based on language
            if lang_code == "hi":
                content.append("| समय / Time | वक्ता / Speaker | पाठ / Text |")
            else:
                content.append("| Time | Speaker | Text |")
            
            content.append("|------|---------|------|")
            
            for segment in transcription["segments"]:
                start_time = segment.get("start_formatted", self.format_timestamp(segment["start"]))
                speaker = segment.get("speaker", "Unknown Speaker")
                text = segment["text"].strip()
                content.append(f"| {start_time} | {speaker} | {text} |")
        
        # Speaker summary
        if "segments" in transcription:
            speakers = set()
            for segment in transcription["segments"]:
                if "speaker" in segment:
                    speakers.add(segment["speaker"])
            
            if len(speakers) > 1:
                if lang_code == "hi":
                    content.append("\n## वक्ताओं की सूची / Speakers List\n")
                else:
                    content.append("\n## Speakers List\n")
                
                for i, speaker in enumerate(sorted(speakers), 1):
                    content.append(f"{i}. {speaker}")
        
        return "\n".join(content)
    
    def process_voice_memo(self, audio_path, output_dir=None):
        """
        Process a single voice memo file with unified language support
        
        Args:
            audio_path (str): Path to audio file
            output_dir (str): Directory to save output files
            
        Returns:
            str: Path to generated markdown file
        """
        try:
            # Get file info
            file_path = Path(audio_path)
            file_name = file_path.stem
            
            # Set output directory
            if not output_dir:
                output_dir = file_path.parent / "transcriptions"
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Check if audio format is supported
            if file_path.suffix.lower() not in self.supported_formats:
                logger.warning(f"Unsupported format: {file_path.suffix}")
                # Try to convert to wav
                audio_path = self.convert_audio_format(audio_path)
                file_path = Path(audio_path)
            
            # Transcribe audio
            transcription = self.transcribe_audio(audio_path)
            
            # Get language info for metadata
            lang_code = self.language
            lang_config = self.language_configs.get(lang_code, self.language_configs["auto"])
            lang_name = lang_config["name"]
            
            # Prepare metadata
            metadata = {
                "File Name": file_name,
                "File Size": f"{file_path.stat().st_size / 1024:.1f} KB",
                "Duration": f"{transcription.get('duration', 'Unknown'):.1f} seconds",
                "Language": lang_name,
                "Language Code": lang_code,
                "Speakers Detected": len(set(seg.get("speaker", "Unknown") for seg in transcription.get("segments", []))),
                "Transcribed At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Save markdown
            output_path = output_dir / f"{file_name}_transcription.md"
            self.save_transcription_markdown(transcription, output_path, metadata)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error processing voice memo {audio_path}: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Unified Voice Transcriber - Multi-language with Speaker Diarization")
    parser.add_argument("input", help="Input audio file or directory")
    parser.add_argument("-o", "--output", help="Output directory for transcriptions")
    parser.add_argument("-m", "--model", default="base", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size (default: base)")
    parser.add_argument("-r", "--recursive", action="store_true", 
                       help="Process directories recursively")
    parser.add_argument("--no-speaker-diarization", action="store_true",
                       help="Disable speaker diarization")
    
    args = parser.parse_args()
    
    try:
        # Initialize transcriber
        transcriber = UnifiedVoiceTranscriber(
            model_size=args.model,
            enable_speaker_diarization=not args.no_speaker_diarization
        )
        
        input_path = Path(args.input)
        
        if input_path.is_file():
            # Process single file
            output_file = transcriber.process_voice_memo(str(input_path), args.output)
            print(f"✓ Transcription saved to: {output_file}")
            
        elif input_path.is_dir():
            # Process directory
            audio_files = []
            
            if args.recursive:
                for ext in transcriber.supported_formats:
                    audio_files.extend(input_path.rglob(f"*{ext}"))
            else:
                for ext in transcriber.supported_formats:
                    audio_files.extend(input_path.glob(f"*{ext}"))
            
            if not audio_files:
                print("No audio files found in the specified directory.")
                return
            
            print(f"Found {len(audio_files)} audio files to process...")
            
            for audio_file in tqdm(audio_files, desc="Processing audio files"):
                try:
                    output_file = transcriber.process_voice_memo(str(audio_file), args.output)
                    print(f"✓ {audio_file.name} -> {output_file}")
                except Exception as e:
                    print(f"✗ Error processing {audio_file.name}: {e}")
            
            print(f"\nCompleted! Processed {len(audio_files)} files.")
            
        else:
            print(f"Error: {args.input} is not a valid file or directory.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
