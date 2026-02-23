"""
Model Validator for Whisper Models
Ensures models are correctly loaded and functioning properly
"""

import os
import time
import logging
import numpy as np
import torch
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

try:
    import whisper
    from whisper.audio import load_audio, pad_or_trim
    from whisper.decoding import DecodingOptions
except ImportError:
    whisper = None
    logging.warning("Whisper not available. Model validation will not work.")

logger = logging.getLogger(__name__)

class ModelValidator:
    """Validates that Whisper models are correctly loaded and functioning"""
    
    def __init__(self):
        self.validation_results = {}
        self.test_audio_samples = {}
        self.validation_config = {
            'test_duration': 5.0,  # seconds
            'sample_rate': 16000,
            'max_validation_time': 60,  # seconds
            'min_accuracy_threshold': 0.7,  # 70% accuracy
            'enable_gpu': os.getenv('ENABLE_GPU_ACCELERATION', 'true').lower() == 'true'
        }
        
        # Create test audio samples
        self._create_test_audio_samples()
    
    def _create_test_audio_samples(self):
        """Create synthetic test audio samples for validation"""
        try:
            # Generate a simple sine wave test audio
            sample_rate = self.validation_config['sample_rate']
            duration = self.validation_config['test_duration']
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            # Create a simple test phrase as audio
            # This is a basic sine wave - in practice, you'd use real audio samples
            frequency = 440  # A4 note
            audio = np.sin(2 * np.pi * frequency * t) * 0.3
            
            # Add some noise to make it more realistic
            noise = np.random.normal(0, 0.05, audio.shape)
            audio = audio + noise
            
            self.test_audio_samples['sine_wave'] = {
                'audio': audio,
                'sample_rate': sample_rate,
                'expected_text': 'test audio',  # Placeholder
                'language': 'en'
            }
            
            # Create a more complex test with multiple frequencies
            complex_audio = np.zeros_like(audio)
            for freq in [220, 330, 440, 550]:  # Multiple harmonics
                complex_audio += np.sin(2 * np.pi * freq * t) * 0.1
            complex_audio += np.random.normal(0, 0.03, complex_audio.shape)
            
            self.test_audio_samples['complex_wave'] = {
                'audio': complex_audio,
                'sample_rate': sample_rate,
                'expected_text': 'complex test',
                'language': 'en'
            }
            
            logger.info("Test audio samples created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create test audio samples: {e}")
    
    def validate_model(self, model_size: str, model_instance: Any = None) -> Dict[str, Any]:
        """
        Validate that a Whisper model is correctly loaded and functioning
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            model_instance: Pre-loaded model instance (optional)
            
        Returns:
            Validation results dictionary
        """
        validation_id = f"{model_size}_{int(time.time())}"
        start_time = time.time()
        
        logger.info(f"Starting validation for model: {model_size}")
        
        results = {
            'model_size': model_size,
            'validation_id': validation_id,
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'tests': {},
            'overall_score': 0.0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test 1: Model Loading
            model_test = self._test_model_loading(model_size, model_instance)
            results['tests']['model_loading'] = model_test
            
            if not model_test['passed']:
                results['status'] = 'failed'
                results['errors'].append("Model loading failed")
                return results
            
            model = model_test['model']
            
            # Test 2: Basic Functionality
            functionality_test = self._test_basic_functionality(model, model_size)
            results['tests']['basic_functionality'] = functionality_test
            
            # Test 3: Audio Processing
            audio_test = self._test_audio_processing(model, model_size)
            results['tests']['audio_processing'] = audio_test
            
            # Test 4: Transcription Quality
            transcription_test = self._test_transcription_quality(model, model_size)
            results['tests']['transcription_quality'] = transcription_test
            
            # Test 5: Performance Metrics
            performance_test = self._test_performance_metrics(model, model_size)
            results['tests']['performance'] = performance_test
            
            # Test 6: Memory Usage
            memory_test = self._test_memory_usage(model, model_size)
            results['tests']['memory_usage'] = memory_test
            
            # Calculate overall score
            test_scores = [test.get('score', 0) for test in results['tests'].values() if 'score' in test]
            results['overall_score'] = sum(test_scores) / len(test_scores) if test_scores else 0
            
            # Determine final status
            if results['overall_score'] >= self.validation_config['min_accuracy_threshold']:
                results['status'] = 'passed'
            else:
                results['status'] = 'failed'
                results['warnings'].append(f"Overall score {results['overall_score']:.2f} below threshold {self.validation_config['min_accuracy_threshold']}")
            
            # Check for critical errors
            critical_tests = ['model_loading', 'basic_functionality']
            for test_name in critical_tests:
                if test_name in results['tests'] and not results['tests'][test_name]['passed']:
                    results['status'] = 'failed'
                    results['errors'].append(f"Critical test failed: {test_name}")
            
        except Exception as e:
            logger.error(f"Validation failed for model {model_size}: {e}")
            results['status'] = 'error'
            results['errors'].append(str(e))
        
        finally:
            results['end_time'] = datetime.now().isoformat()
            results['duration'] = time.time() - start_time
            
            # Store results
            self.validation_results[validation_id] = results
            
            logger.info(f"Validation completed for {model_size}: {results['status']} (score: {results['overall_score']:.2f})")
        
        return results
    
    def _test_model_loading(self, model_size: str, model_instance: Any = None) -> Dict[str, Any]:
        """Test model loading and basic properties"""
        test_result = {
            'name': 'Model Loading',
            'passed': False,
            'score': 0.0,
            'details': {},
            'errors': []
        }
        
        try:
            if model_instance is not None:
                model = model_instance
                test_result['details']['source'] = 'provided_instance'
            else:
                # Load model
                device = "cuda" if self.validation_config['enable_gpu'] and torch.cuda.is_available() else "cpu"
                model = whisper.load_model(model_size, device=device)
                test_result['details']['source'] = 'loaded_fresh'
            
            # Check model properties
            test_result['details']['device'] = str(next(model.parameters()).device)
            test_result['details']['model_size'] = model_size
            test_result['details']['parameters'] = sum(p.numel() for p in model.parameters())
            
            # Check if model has required methods
            required_methods = ['transcribe', 'encode', 'decode']
            missing_methods = [method for method in required_methods if not hasattr(model, method)]
            
            if missing_methods:
                test_result['errors'].append(f"Missing methods: {missing_methods}")
            else:
                test_result['passed'] = True
                test_result['score'] = 1.0
                test_result['details']['methods_available'] = required_methods
            
        except Exception as e:
            test_result['errors'].append(str(e))
            logger.error(f"Model loading test failed: {e}")
        
        return test_result
    
    def _test_basic_functionality(self, model: Any, model_size: str) -> Dict[str, Any]:
        """Test basic model functionality"""
        test_result = {
            'name': 'Basic Functionality',
            'passed': False,
            'score': 0.0,
            'details': {},
            'errors': []
        }
        
        try:
            # Test with minimal audio
            sample_rate = self.validation_config['sample_rate']
            duration = 1.0  # 1 second test
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            test_audio = np.sin(2 * np.pi * 440 * t) * 0.1  # Quiet sine wave
            
            # Test transcribe method
            start_time = time.time()
            result = model.transcribe(test_audio)
            transcribe_time = time.time() - start_time
            
            test_result['details']['transcribe_time'] = transcribe_time
            test_result['details']['result_type'] = type(result).__name__
            
            # Check result structure
            if isinstance(result, dict) and 'text' in result:
                test_result['details']['has_text'] = True
                test_result['details']['text_length'] = len(result['text'])
                test_result['passed'] = True
                test_result['score'] = 1.0
            else:
                test_result['errors'].append("Invalid transcribe result structure")
            
        except Exception as e:
            test_result['errors'].append(str(e))
            logger.error(f"Basic functionality test failed: {e}")
        
        return test_result
    
    def _test_audio_processing(self, model: Any, model_size: str) -> Dict[str, Any]:
        """Test audio processing capabilities"""
        test_result = {
            'name': 'Audio Processing',
            'passed': False,
            'score': 0.0,
            'details': {},
            'errors': []
        }
        
        try:
            # Test with different audio samples
            for sample_name, sample_data in self.test_audio_samples.items():
                audio = sample_data['audio']
                sample_rate = sample_data['sample_rate']
                
                # Test audio preprocessing
                start_time = time.time()
                result = model.transcribe(audio)
                process_time = time.time() - start_time
                
                test_result['details'][f'{sample_name}_process_time'] = process_time
                test_result['details'][f'{sample_name}_text_length'] = len(result.get('text', ''))
            
            test_result['passed'] = True
            test_result['score'] = 1.0
            
        except Exception as e:
            test_result['errors'].append(str(e))
            logger.error(f"Audio processing test failed: {e}")
        
        return test_result
    
    def _test_transcription_quality(self, model: Any, model_size: str) -> Dict[str, Any]:
        """Test transcription quality with known audio samples"""
        test_result = {
            'name': 'Transcription Quality',
            'passed': False,
            'score': 0.0,
            'details': {},
            'errors': []
        }
        
        try:
            # This is a simplified test - in practice, you'd use real audio samples
            # with known transcriptions for accurate quality assessment
            
            sample = self.test_audio_samples['sine_wave']
            audio = sample['audio']
            
            result = model.transcribe(audio, language='en')
            transcribed_text = result.get('text', '').strip().lower()
            
            # Basic quality checks
            quality_score = 0.0
            
            # Check if transcription produces some output
            if len(transcribed_text) > 0:
                quality_score += 0.3
                test_result['details']['has_output'] = True
            
            # Check for reasonable length (not too short, not too long)
            if 1 <= len(transcribed_text) <= 100:
                quality_score += 0.3
                test_result['details']['reasonable_length'] = True
            
            # Check for common transcription artifacts
            artifacts = ['<|', '|>', '♪', '♫']
            has_artifacts = any(artifact in transcribed_text for artifact in artifacts)
            if not has_artifacts:
                quality_score += 0.2
                test_result['details']['no_artifacts'] = True
            
            # Check for language consistency (basic check)
            if any(char.isalpha() for char in transcribed_text):
                quality_score += 0.2
                test_result['details']['has_letters'] = True
            
            test_result['score'] = quality_score
            test_result['details']['transcribed_text'] = transcribed_text
            test_result['details']['quality_score'] = quality_score
            
            if quality_score >= 0.5:  # 50% quality threshold
                test_result['passed'] = True
            
        except Exception as e:
            test_result['errors'].append(str(e))
            logger.error(f"Transcription quality test failed: {e}")
        
        return test_result
    
    def _test_performance_metrics(self, model: Any, model_size: str) -> Dict[str, Any]:
        """Test performance metrics"""
        test_result = {
            'name': 'Performance Metrics',
            'passed': False,
            'score': 0.0,
            'details': {},
            'errors': []
        }
        
        try:
            sample = self.test_audio_samples['sine_wave']
            audio = sample['audio']
            duration = len(audio) / sample['sample_rate']
            
            # Measure transcription speed
            start_time = time.time()
            result = model.transcribe(audio)
            total_time = time.time() - start_time
            
            # Calculate metrics
            real_time_factor = total_time / duration
            words_per_second = len(result.get('text', '').split()) / total_time if total_time > 0 else 0
            
            test_result['details']['total_time'] = total_time
            test_result['details']['audio_duration'] = duration
            test_result['details']['real_time_factor'] = real_time_factor
            test_result['details']['words_per_second'] = words_per_second
            
            # Performance scoring
            score = 0.0
            
            # Real-time factor should be reasonable (not too slow)
            if real_time_factor <= 2.0:  # 2x real-time or faster
                score += 0.5
                test_result['details']['speed_acceptable'] = True
            
            # Should process audio without errors
            if total_time < self.validation_config['max_validation_time']:
                score += 0.3
                test_result['details']['within_timeout'] = True
            
            # Should produce some output
            if len(result.get('text', '')) > 0:
                score += 0.2
                test_result['details']['produces_output'] = True
            
            test_result['score'] = score
            test_result['passed'] = score >= 0.7
            
        except Exception as e:
            test_result['errors'].append(str(e))
            logger.error(f"Performance metrics test failed: {e}")
        
        return test_result
    
    def _test_memory_usage(self, model: Any, model_size: str) -> Dict[str, Any]:
        """Test memory usage"""
        test_result = {
            'name': 'Memory Usage',
            'passed': False,
            'score': 0.0,
            'details': {},
            'errors': []
        }
        
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Get model memory usage
            model_memory = 0
            for param in model.parameters():
                model_memory += param.numel() * param.element_size()
            
            test_result['details']['rss_mb'] = memory_info.rss / 1024 / 1024
            test_result['details']['vms_mb'] = memory_info.vms / 1024 / 1024
            test_result['details']['model_memory_mb'] = model_memory / 1024 / 1024
            test_result['details']['memory_percent'] = process.memory_percent()
            
            # Memory scoring
            score = 0.0
            
            # Memory usage should be reasonable
            if memory_info.rss / 1024 / 1024 < 2000:  # Less than 2GB
                score += 0.5
                test_result['details']['memory_reasonable'] = True
            
            # Memory percentage should be reasonable
            if process.memory_percent() < 80:
                score += 0.3
                test_result['details']['memory_percent_ok'] = True
            
            # Model should have loaded successfully
            if model_memory > 0:
                score += 0.2
                test_result['details']['model_loaded'] = True
            
            test_result['score'] = score
            test_result['passed'] = score >= 0.7
            
        except ImportError:
            test_result['errors'].append("psutil not available for memory testing")
        except Exception as e:
            test_result['errors'].append(str(e))
            logger.error(f"Memory usage test failed: {e}")
        
        return test_result
    
    def validate_all_models(self, model_sizes: List[str]) -> Dict[str, Any]:
        """Validate all specified models"""
        results = {
            'start_time': datetime.now().isoformat(),
            'models': {},
            'overall_status': 'running',
            'summary': {}
        }
        
        try:
            for model_size in model_sizes:
                logger.info(f"Validating model: {model_size}")
                model_result = self.validate_model(model_size)
                results['models'][model_size] = model_result
            
            # Calculate summary
            passed_models = [size for size, result in results['models'].items() if result['status'] == 'passed']
            failed_models = [size for size, result in results['models'].items() if result['status'] == 'failed']
            
            results['summary'] = {
                'total_models': len(model_sizes),
                'passed_models': len(passed_models),
                'failed_models': len(failed_models),
                'passed_list': passed_models,
                'failed_list': failed_models,
                'average_score': sum(result['overall_score'] for result in results['models'].values()) / len(model_sizes)
            }
            
            if len(passed_models) == len(model_sizes):
                results['overall_status'] = 'passed'
            elif len(passed_models) > 0:
                results['overall_status'] = 'partial'
            else:
                results['overall_status'] = 'failed'
            
        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            results['overall_status'] = 'error'
            results['error'] = str(e)
        
        finally:
            results['end_time'] = datetime.now().isoformat()
        
        return results
    
    def get_validation_results(self, validation_id: str = None) -> Dict[str, Any]:
        """Get validation results"""
        if validation_id:
            return self.validation_results.get(validation_id, {})
        return self.validation_results
    
    def save_validation_report(self, results: Dict[str, Any], filepath: str = None):
        """Save validation results to file"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"model_validation_report_{timestamp}.json"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Validation report saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")

# Global model validator instance
model_validator = ModelValidator()

def get_model_validator() -> ModelValidator:
    """Get the global model validator instance"""
    return model_validator
