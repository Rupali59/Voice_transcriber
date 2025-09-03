"""
Test audio file fixtures for Voice Transcriber tests
Provides sample audio files and utilities for testing
"""

import os
import tempfile
import wave
import numpy as np
from pathlib import Path


class TestAudioFixtures:
    """Test audio file fixtures and utilities"""
    
    @staticmethod
    def create_test_wav_file(duration=5, sample_rate=16000, filename=None):
        """
        Create a test WAV file with specified duration
        
        Args:
            duration: Duration in seconds
            sample_rate: Sample rate in Hz
            filename: Output filename (optional)
            
        Returns:
            str: Path to created WAV file
        """
        if filename is None:
            filename = f"test_audio_{duration}s.wav"
        
        # Create temporary directory if needed
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        
        # Generate test audio (sine wave)
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        frequency = 440  # A4 note
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return filepath
    
    @staticmethod
    def create_test_mp3_file(duration=5, filename=None):
        """
        Create a test MP3 file (placeholder - would need actual MP3 encoding)
        
        Args:
            duration: Duration in seconds
            filename: Output filename (optional)
            
        Returns:
            str: Path to created MP3 file
        """
        if filename is None:
            filename = f"test_audio_{duration}s.mp3"
        
        # Create temporary directory if needed
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        
        # For testing purposes, create a dummy MP3 file
        # In real implementation, would use proper MP3 encoding
        with open(filepath, 'wb') as f:
            f.write(b'ID3\x03\x00\x00\x00\x00\x00\x00\x00')  # MP3 header
            f.write(b'\x00' * 1024)  # Dummy data
        
        return filepath
    
    @staticmethod
    def create_test_m4a_file(duration=5, filename=None):
        """
        Create a test M4A file (placeholder - would need actual M4A encoding)
        
        Args:
            duration: Duration in seconds
            filename: Output filename (optional)
            
        Returns:
            str: Path to created M4A file
        """
        if filename is None:
            filename = f"test_audio_{duration}s.m4a"
        
        # Create temporary directory if needed
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        
        # For testing purposes, create a dummy M4A file
        # In real implementation, would use proper M4A encoding
        with open(filepath, 'wb') as f:
            f.write(b'ftypM4A ')  # M4A header
            f.write(b'\x00' * 1024)  # Dummy data
        
        return filepath
    
    @staticmethod
    def create_silent_audio_file(duration=5, sample_rate=16000, filename=None):
        """
        Create a silent audio file for testing
        
        Args:
            duration: Duration in seconds
            sample_rate: Sample rate in Hz
            filename: Output filename (optional)
            
        Returns:
            str: Path to created WAV file
        """
        if filename is None:
            filename = f"silent_audio_{duration}s.wav"
        
        # Create temporary directory if needed
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        
        # Generate silent audio
        audio_data = np.zeros(int(sample_rate * duration), dtype=np.int16)
        
        # Write WAV file
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return filepath
    
    @staticmethod
    def create_noisy_audio_file(duration=5, sample_rate=16000, noise_level=0.1, filename=None):
        """
        Create a noisy audio file for testing
        
        Args:
            duration: Duration in seconds
            sample_rate: Sample rate in Hz
            noise_level: Noise level (0.0 to 1.0)
            filename: Output filename (optional)
            
        Returns:
            str: Path to created WAV file
        """
        if filename is None:
            filename = f"noisy_audio_{duration}s.wav"
        
        # Create temporary directory if needed
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        
        # Generate test audio with noise
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        frequency = 440  # A4 note
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Add noise
        noise = np.random.normal(0, noise_level, len(audio_data))
        audio_data = audio_data + noise
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return filepath
    
    @staticmethod
    def create_multi_speaker_audio_file(duration=10, sample_rate=16000, num_speakers=2, filename=None):
        """
        Create a multi-speaker audio file for testing speaker diarization
        
        Args:
            duration: Duration in seconds
            sample_rate: Sample rate in Hz
            num_speakers: Number of speakers
            filename: Output filename (optional)
            
        Returns:
            str: Path to created WAV file
        """
        if filename is None:
            filename = f"multi_speaker_{num_speakers}_{duration}s.wav"
        
        # Create temporary directory if needed
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        
        # Generate multi-speaker audio
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.zeros(len(t), dtype=np.float32)
        
        # Each speaker gets a different frequency and time segment
        segment_duration = duration / num_speakers
        frequencies = [440, 523, 659, 784]  # A4, C5, E5, G5
        
        for i in range(num_speakers):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration
            
            start_idx = int(start_time * sample_rate)
            end_idx = int(end_time * sample_rate)
            
            if end_idx > len(t):
                end_idx = len(t)
            
            segment_t = t[start_idx:end_idx]
            frequency = frequencies[i % len(frequencies)]
            segment_audio = np.sin(2 * np.pi * frequency * segment_t)
            
            audio_data[start_idx:end_idx] = segment_audio
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return filepath
    
    @staticmethod
    def create_large_audio_file(duration=300, sample_rate=16000, filename=None):
        """
        Create a large audio file for testing performance
        
        Args:
            duration: Duration in seconds (default 5 minutes)
            sample_rate: Sample rate in Hz
            filename: Output filename (optional)
            
        Returns:
            str: Path to created WAV file
        """
        if filename is None:
            filename = f"large_audio_{duration}s.wav"
        
        # Create temporary directory if needed
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, filename)
        
        # Generate large audio file
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        frequency = 440  # A4 note
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return filepath
    
    @staticmethod
    def cleanup_test_files(filepaths):
        """
        Clean up test files and directories
        
        Args:
            filepaths: List of file paths to clean up
        """
        for filepath in filepaths:
            if os.path.exists(filepath):
                os.remove(filepath)
                # Remove parent directory if empty
                parent_dir = os.path.dirname(filepath)
                try:
                    os.rmdir(parent_dir)
                except OSError:
                    pass  # Directory not empty or doesn't exist
    
    @staticmethod
    def get_test_file_info(filepath):
        """
        Get information about a test audio file
        
        Args:
            filepath: Path to audio file
            
        Returns:
            dict: File information
        """
        if not os.path.exists(filepath):
            return None
        
        file_size = os.path.getsize(filepath)
        
        # Try to get audio info if it's a WAV file
        audio_info = {}
        if filepath.lower().endswith('.wav'):
            try:
                with wave.open(filepath, 'r') as wav_file:
                    audio_info = {
                        'channels': wav_file.getnchannels(),
                        'sample_width': wav_file.getsampwidth(),
                        'sample_rate': wav_file.getframerate(),
                        'frames': wav_file.getnframes(),
                        'duration': wav_file.getnframes() / wav_file.getframerate()
                    }
            except Exception:
                pass
        
        return {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'file_size': file_size,
            'file_size_mb': file_size / (1024 * 1024),
            'audio_info': audio_info
        }


# Predefined test files for common test scenarios
class TestAudioFiles:
    """Predefined test audio files for common scenarios"""
    
    @staticmethod
    def get_short_audio():
        """Get a short audio file (5 seconds)"""
        return TestAudioFixtures.create_test_wav_file(duration=5)
    
    @staticmethod
    def get_medium_audio():
        """Get a medium audio file (30 seconds)"""
        return TestAudioFixtures.create_test_wav_file(duration=30)
    
    @staticmethod
    def get_long_audio():
        """Get a long audio file (2 minutes)"""
        return TestAudioFixtures.create_test_wav_file(duration=120)
    
    @staticmethod
    def get_silent_audio():
        """Get a silent audio file"""
        return TestAudioFixtures.create_silent_audio_file(duration=10)
    
    @staticmethod
    def get_noisy_audio():
        """Get a noisy audio file"""
        return TestAudioFixtures.create_noisy_audio_file(duration=10, noise_level=0.2)
    
    @staticmethod
    def get_multi_speaker_audio():
        """Get a multi-speaker audio file"""
        return TestAudioFixtures.create_multi_speaker_audio_file(duration=20, num_speakers=3)
    
    @staticmethod
    def get_large_audio():
        """Get a large audio file for performance testing"""
        return TestAudioFixtures.create_large_audio_file(duration=300)
    
    @staticmethod
    def get_all_test_files():
        """Get all predefined test files"""
        return [
            TestAudioFiles.get_short_audio(),
            TestAudioFiles.get_medium_audio(),
            TestAudioFiles.get_long_audio(),
            TestAudioFiles.get_silent_audio(),
            TestAudioFiles.get_noisy_audio(),
            TestAudioFiles.get_multi_speaker_audio(),
            TestAudioFiles.get_large_audio()
        ]
