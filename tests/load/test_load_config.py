"""
Load Testing Configuration for Voice Transcriber
Configuration and utilities for load testing scenarios
"""

import os
import json
import time
import threading
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class LoadTestScenario:
    """Configuration for a load test scenario"""
    name: str
    description: str
    concurrent_users: int
    duration_seconds: int
    requests_per_user: int
    ramp_up_seconds: int
    ramp_down_seconds: int
    target_endpoints: List[str]
    file_size_mb: float
    model_size: str
    enable_speaker_diarization: bool
    language: str
    expected_success_rate: float
    expected_avg_response_time: float
    expected_max_response_time: float


@dataclass
class LoadTestResult:
    """Results from a load test"""
    scenario_name: str
    start_time: float
    end_time: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    requests_per_second: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    min_response_time: float
    errors: List[str]
    response_times: List[float]


class LoadTestConfig:
    """Load testing configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "load_test_config.json"
        self.scenarios = self._load_scenarios()
        self.results = []
    
    def _load_scenarios(self) -> List[LoadTestScenario]:
        """Load test scenarios from configuration"""
        default_scenarios = [
            LoadTestScenario(
                name="light_load",
                description="Light load test with few users",
                concurrent_users=5,
                duration_seconds=60,
                requests_per_user=10,
                ramp_up_seconds=10,
                ramp_down_seconds=10,
                target_endpoints=["/health", "/api/models", "/api/cache/stats"],
                file_size_mb=1.0,
                model_size="tiny",
                enable_speaker_diarization=False,
                language="en",
                expected_success_rate=99.0,
                expected_avg_response_time=1.0,
                expected_max_response_time=5.0
            ),
            LoadTestScenario(
                name="medium_load",
                description="Medium load test with moderate users",
                concurrent_users=20,
                duration_seconds=120,
                requests_per_user=20,
                ramp_up_seconds=20,
                ramp_down_seconds=20,
                target_endpoints=["/api/upload", "/api/transcribe", "/api/job"],
                file_size_mb=5.0,
                model_size="base",
                enable_speaker_diarization=True,
                language="en",
                expected_success_rate=95.0,
                expected_avg_response_time=2.0,
                expected_max_response_time=10.0
            ),
            LoadTestScenario(
                name="heavy_load",
                description="Heavy load test with many users",
                concurrent_users=50,
                duration_seconds=300,
                requests_per_user=30,
                ramp_up_seconds=30,
                ramp_down_seconds=30,
                target_endpoints=["/api/upload", "/api/transcribe", "/api/job", "/api/cache/stats"],
                file_size_mb=10.0,
                model_size="small",
                enable_speaker_diarization=True,
                language="en",
                expected_success_rate=90.0,
                expected_avg_response_time=3.0,
                expected_max_response_time=15.0
            ),
            LoadTestScenario(
                name="stress_test",
                description="Stress test to find system limits",
                concurrent_users=100,
                duration_seconds=600,
                requests_per_user=50,
                ramp_up_seconds=60,
                ramp_down_seconds=60,
                target_endpoints=["/api/upload", "/api/transcribe", "/api/job"],
                file_size_mb=20.0,
                model_size="medium",
                enable_speaker_diarization=True,
                language="en",
                expected_success_rate=80.0,
                expected_avg_response_time=5.0,
                expected_max_response_time=30.0
            ),
            LoadTestScenario(
                name="spike_test",
                description="Spike test with sudden load increase",
                concurrent_users=200,
                duration_seconds=180,
                requests_per_user=10,
                ramp_up_seconds=5,
                ramp_down_seconds=5,
                target_endpoints=["/health", "/api/models", "/api/cache/stats"],
                file_size_mb=2.0,
                model_size="tiny",
                enable_speaker_diarization=False,
                language="en",
                expected_success_rate=85.0,
                expected_avg_response_time=2.0,
                expected_max_response_time=10.0
            ),
            LoadTestScenario(
                name="endurance_test",
                description="Endurance test for long-term stability",
                concurrent_users=30,
                duration_seconds=3600,  # 1 hour
                requests_per_user=100,
                ramp_up_seconds=300,
                ramp_down_seconds=300,
                target_endpoints=["/api/upload", "/api/transcribe", "/api/job"],
                file_size_mb=5.0,
                model_size="base",
                enable_speaker_diarization=True,
                language="en",
                expected_success_rate=95.0,
                expected_avg_response_time=2.5,
                expected_max_response_time=12.0
            )
        ]
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    scenarios = []
                    for scenario_data in config_data.get('scenarios', []):
                        scenarios.append(LoadTestScenario(**scenario_data))
                    return scenarios
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
                print("Using default scenarios")
        
        return default_scenarios
    
    def save_scenarios(self):
        """Save scenarios to configuration file"""
        config_data = {
            'scenarios': [asdict(scenario) for scenario in self.scenarios]
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get_scenario(self, name: str) -> Optional[LoadTestScenario]:
        """Get a specific scenario by name"""
        for scenario in self.scenarios:
            if scenario.name == name:
                return scenario
        return None
    
    def list_scenarios(self) -> List[str]:
        """List all available scenario names"""
        return [scenario.name for scenario in self.scenarios]
    
    def add_result(self, result: LoadTestResult):
        """Add a test result"""
        self.results.append(result)
    
    def get_results(self) -> List[LoadTestResult]:
        """Get all test results"""
        return self.results
    
    def save_results(self, filename: Optional[str] = None):
        """Save test results to file"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"
        
        results_data = {
            'timestamp': time.time(),
            'results': [asdict(result) for result in self.results]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"Results saved to {filename}")
    
    def generate_report(self) -> str:
        """Generate a text report of all results"""
        if not self.results:
            return "No test results available"
        
        report = []
        report.append("=" * 80)
        report.append("LOAD TEST RESULTS SUMMARY")
        report.append("=" * 80)
        report.append("")
        
        for result in self.results:
            report.append(f"Scenario: {result.scenario_name}")
            report.append(f"Duration: {result.end_time - result.start_time:.2f} seconds")
            report.append(f"Total Requests: {result.total_requests}")
            report.append(f"Successful: {result.successful_requests} ({result.success_rate:.1f}%)")
            report.append(f"Failed: {result.failed_requests}")
            report.append(f"Requests/sec: {result.requests_per_second:.2f}")
            report.append(f"Avg Response Time: {result.avg_response_time:.3f}s")
            report.append(f"Median Response Time: {result.median_response_time:.3f}s")
            report.append(f"95th Percentile: {result.p95_response_time:.3f}s")
            report.append(f"99th Percentile: {result.p99_response_time:.3f}s")
            report.append(f"Max Response Time: {result.max_response_time:.3f}s")
            
            if result.errors:
                report.append(f"Errors: {len(result.errors)}")
                unique_errors = list(set(result.errors))
                for error in unique_errors[:5]:  # Show first 5 unique errors
                    report.append(f"  - {error}")
            
            report.append("")
            report.append("-" * 40)
            report.append("")
        
        return "\n".join(report)


class LoadTestMonitor:
    """Monitor system resources during load tests"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start monitoring system resources"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring system resources"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Monitoring loop"""
        try:
            import psutil
        except ImportError:
            print("Warning: psutil not available for monitoring")
            return
        
        while self.monitoring:
            try:
                timestamp = time.time()
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                metric = {
                    'timestamp': timestamp,
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_mb': memory.used / (1024 * 1024),
                    'disk_percent': disk.percent,
                    'disk_used_mb': disk.used / (1024 * 1024)
                }
                
                self.metrics.append(metric)
                time.sleep(1)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(1)
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """Get collected metrics"""
        return self.metrics.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of metrics"""
        if not self.metrics:
            return {}
        
        cpu_values = [m['cpu_percent'] for m in self.metrics]
        memory_values = [m['memory_percent'] for m in self.metrics]
        disk_values = [m['disk_percent'] for m in self.metrics]
        
        return {
            'duration_seconds': self.metrics[-1]['timestamp'] - self.metrics[0]['timestamp'],
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_max': max(cpu_values),
            'memory_avg': sum(memory_values) / len(memory_values),
            'memory_max': max(memory_values),
            'disk_avg': sum(disk_values) / len(disk_values),
            'disk_max': max(disk_values)
        }


# Environment configuration
class LoadTestEnvironment:
    """Load test environment configuration"""
    
    @staticmethod
    def get_base_url() -> str:
        """Get base URL for testing"""
        return os.getenv('TEST_BASE_URL', 'http://localhost:5001')
    
    @staticmethod
    def get_test_data_dir() -> str:
        """Get test data directory"""
        return os.getenv('TEST_DATA_DIR', 'tests/fixtures')
    
    @staticmethod
    def get_results_dir() -> str:
        """Get results directory"""
        return os.getenv('TEST_RESULTS_DIR', 'tests/results')
    
    @staticmethod
    def setup_environment():
        """Set up test environment"""
        # Create results directory
        results_dir = LoadTestEnvironment.get_results_dir()
        os.makedirs(results_dir, exist_ok=True)
        
        # Set up logging
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{results_dir}/load_test.log'),
                logging.StreamHandler()
            ]
        )
    
    @staticmethod
    def cleanup_environment():
        """Clean up test environment"""
        # Clean up temporary files
        import tempfile
        import shutil
        
        temp_dir = tempfile.gettempdir()
        for item in os.listdir(temp_dir):
            if item.startswith('voice_transcriber_test_'):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception:
                    pass


if __name__ == '__main__':
    # Example usage
    config = LoadTestConfig()
    
    print("Available scenarios:")
    for scenario_name in config.list_scenarios():
        scenario = config.get_scenario(scenario_name)
        print(f"  - {scenario_name}: {scenario.description}")
    
    # Save default configuration
    config.save_scenarios()
    print(f"\nConfiguration saved to {config.config_file}")
