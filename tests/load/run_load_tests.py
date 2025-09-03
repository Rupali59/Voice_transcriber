#!/usr/bin/env python3
"""
Load Testing Runner for Voice Transcriber
Comprehensive load testing with configurable scenarios
"""

import sys
import os
import time
import argparse
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import statistics

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.load.test_load_config import LoadTestConfig, LoadTestScenario, LoadTestResult, LoadTestMonitor, LoadTestEnvironment
from tests.fixtures.test_audio_files import TestAudioFixtures
import requests


class LoadTestRunner:
    """Main load test runner"""
    
    def __init__(self, config_file: str = None):
        self.config = LoadTestConfig(config_file)
        self.monitor = LoadTestMonitor()
        self.results = []
    
    def run_scenario(self, scenario_name: str) -> LoadTestResult:
        """Run a specific load test scenario"""
        scenario = self.config.get_scenario(scenario_name)
        if not scenario:
            raise ValueError(f"Scenario '{scenario_name}' not found")
        
        print(f"\n🚀 Running Load Test Scenario: {scenario.name}")
        print(f"   Description: {scenario.description}")
        print(f"   Concurrent Users: {scenario.concurrent_users}")
        print(f"   Duration: {scenario.duration_seconds}s")
        print(f"   Requests per User: {scenario.requests_per_user}")
        print("=" * 60)
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Run the test
        result = self._execute_scenario(scenario)
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Add system metrics to result
        system_metrics = self.monitor.get_summary()
        result.system_metrics = system_metrics
        
        # Save result
        self.config.add_result(result)
        self.results.append(result)
        
        # Print results
        self._print_scenario_results(result)
        
        return result
    
    def run_all_scenarios(self):
        """Run all configured scenarios"""
        print("🎯 Running All Load Test Scenarios")
        print("=" * 60)
        
        for scenario_name in self.config.list_scenarios():
            try:
                self.run_scenario(scenario_name)
                time.sleep(5)  # Brief pause between scenarios
            except Exception as e:
                print(f"❌ Scenario {scenario_name} failed: {e}")
        
        # Generate final report
        self._generate_final_report()
    
    def _execute_scenario(self, scenario: LoadTestScenario) -> LoadTestResult:
        """Execute a load test scenario"""
        start_time = time.time()
        end_time = start_time + scenario.duration_seconds
        
        # Create test audio file
        test_audio_file = TestAudioFixtures.create_test_wav_file(
            duration=30,
            filename=f"load_test_{scenario.name}.wav"
        )
        
        try:
            # Initialize result tracking
            result = LoadTestResult(
                scenario_name=scenario.name,
                start_time=start_time,
                end_time=end_time,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                success_rate=0.0,
                requests_per_second=0.0,
                avg_response_time=0.0,
                median_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                max_response_time=0.0,
                min_response_time=0.0,
                errors=[],
                response_times=[]
            )
            
            # Ramp up phase
            if scenario.ramp_up_seconds > 0:
                print(f"   📈 Ramping up over {scenario.ramp_up_seconds}s...")
                self._ramp_up_phase(scenario, test_audio_file, result, scenario.ramp_up_seconds)
            
            # Steady state phase
            steady_duration = scenario.duration_seconds - scenario.ramp_up_seconds - scenario.ramp_down_seconds
            if steady_duration > 0:
                print(f"   ⚡ Steady state for {steady_duration}s...")
                self._steady_state_phase(scenario, test_audio_file, result, steady_duration)
            
            # Ramp down phase
            if scenario.ramp_down_seconds > 0:
                print(f"   📉 Ramping down over {scenario.ramp_down_seconds}s...")
                self._ramp_down_phase(scenario, test_audio_file, result, scenario.ramp_down_seconds)
            
            # Calculate final metrics
            result.end_time = time.time()
            self._calculate_metrics(result)
            
            return result
            
        finally:
            # Clean up test file
            if os.path.exists(test_audio_file):
                os.remove(test_audio_file)
                parent_dir = os.path.dirname(test_audio_file)
                try:
                    os.rmdir(parent_dir)
                except OSError:
                    pass
    
    def _ramp_up_phase(self, scenario: LoadTestScenario, test_audio_file: str, result: LoadTestResult, duration: int):
        """Ramp up phase - gradually increase load"""
        ramp_up_duration = duration
        users_per_second = scenario.concurrent_users / ramp_up_duration
        
        current_users = 0
        start_time = time.time()
        
        while time.time() - start_time < ramp_up_duration:
            # Add more users
            users_to_add = int(users_per_second)
            if users_to_add > 0:
                current_users = min(current_users + users_to_add, scenario.concurrent_users)
                
                # Start new user threads
                with ThreadPoolExecutor(max_workers=current_users) as executor:
                    futures = []
                    for _ in range(users_to_add):
                        future = executor.submit(self._user_worker, scenario, test_audio_file, result)
                        futures.append(future)
                    
                    # Wait for batch completion
                    for future in as_completed(futures):
                        try:
                            future.result(timeout=30)
                        except Exception as e:
                            result.errors.append(str(e))
            
            time.sleep(1)
    
    def _steady_state_phase(self, scenario: LoadTestScenario, test_audio_file: str, result: LoadTestResult, duration: int):
        """Steady state phase - maintain constant load"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            with ThreadPoolExecutor(max_workers=scenario.concurrent_users) as executor:
                futures = []
                for _ in range(scenario.concurrent_users):
                    future = executor.submit(self._user_worker, scenario, test_audio_file, result)
                    futures.append(future)
                
                # Wait for batch completion
                for future in as_completed(futures):
                    try:
                        future.result(timeout=30)
                    except Exception as e:
                        result.errors.append(str(e))
            
            time.sleep(1)
    
    def _ramp_down_phase(self, scenario: LoadTestScenario, test_audio_file: str, result: LoadTestResult, duration: int):
        """Ramp down phase - gradually decrease load"""
        ramp_down_duration = duration
        users_per_second = scenario.concurrent_users / ramp_down_duration
        
        current_users = scenario.concurrent_users
        start_time = time.time()
        
        while time.time() - start_time < ramp_down_duration and current_users > 0:
            # Reduce users
            users_to_remove = int(users_per_second)
            current_users = max(current_users - users_to_remove, 0)
            
            # Run with reduced users
            if current_users > 0:
                with ThreadPoolExecutor(max_workers=current_users) as executor:
                    futures = []
                    for _ in range(current_users):
                        future = executor.submit(self._user_worker, scenario, test_audio_file, result)
                        futures.append(future)
                    
                    # Wait for batch completion
                    for future in as_completed(futures):
                        try:
                            future.result(timeout=30)
                        except Exception as e:
                            result.errors.append(str(e))
            
            time.sleep(1)
    
    def _user_worker(self, scenario: LoadTestScenario, test_audio_file: str, result: LoadTestResult):
        """Worker function for a single user"""
        for _ in range(scenario.requests_per_user):
            try:
                # Choose random endpoint
                import random
                endpoint = random.choice(scenario.target_endpoints)
                
                start_time = time.time()
                
                if endpoint == "/api/upload":
                    response = self._upload_file_request(test_audio_file)
                elif endpoint == "/api/transcribe":
                    response = self._transcribe_request()
                elif endpoint == "/api/job":
                    response = self._job_status_request()
                else:
                    response = self._generic_request(endpoint)
                
                response_time = time.time() - start_time
                
                # Update result
                result.total_requests += 1
                result.response_times.append(response_time)
                
                if response.status_code in [200, 201]:
                    result.successful_requests += 1
                else:
                    result.failed_requests += 1
                    result.errors.append(f"HTTP {response.status_code}: {response.text[:100]}")
                
            except Exception as e:
                result.total_requests += 1
                result.failed_requests += 1
                result.errors.append(str(e))
                result.response_times.append(30.0)  # Timeout value
            
            # Small delay between requests
            time.sleep(0.1)
    
    def _upload_file_request(self, test_audio_file: str):
        """Upload file request"""
        with open(test_audio_file, 'rb') as f:
            files = {'file': ('test.wav', f, 'audio/wav')}
            return requests.post(f"{LoadTestEnvironment.get_base_url()}/api/upload", files=files, timeout=30)
    
    def _transcribe_request(self):
        """Transcribe request"""
        data = {
            'filename': 'test.wav',
            'model_size': 'base',
            'enable_speaker_diarization': True,
            'language': 'en'
        }
        return requests.post(f"{LoadTestEnvironment.get_base_url()}/api/transcribe", json=data, timeout=30)
    
    def _job_status_request(self):
        """Job status request"""
        return requests.get(f"{LoadTestEnvironment.get_base_url()}/api/job/test-job", timeout=10)
    
    def _generic_request(self, endpoint: str):
        """Generic request"""
        return requests.get(f"{LoadTestEnvironment.get_base_url()}{endpoint}", timeout=10)
    
    def _calculate_metrics(self, result: LoadTestResult):
        """Calculate final metrics"""
        if result.total_requests > 0:
            result.success_rate = (result.successful_requests / result.total_requests) * 100
            result.requests_per_second = result.total_requests / (result.end_time - result.start_time)
        
        if result.response_times:
            result.avg_response_time = statistics.mean(result.response_times)
            result.median_response_time = statistics.median(result.response_times)
            result.max_response_time = max(result.response_times)
            result.min_response_time = min(result.response_times)
            
            # Calculate percentiles
            sorted_times = sorted(result.response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            
            result.p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
            result.p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1]
    
    def _print_scenario_results(self, result: LoadTestResult):
        """Print results for a scenario"""
        print(f"\n📊 Results for {result.scenario_name}:")
        print(f"   Duration: {result.end_time - result.start_time:.2f} seconds")
        print(f"   Total Requests: {result.total_requests}")
        print(f"   Successful: {result.successful_requests} ({result.success_rate:.1f}%)")
        print(f"   Failed: {result.failed_requests}")
        print(f"   Requests/sec: {result.requests_per_second:.2f}")
        print(f"   Avg Response Time: {result.avg_response_time:.3f}s")
        print(f"   Median Response Time: {result.median_response_time:.3f}s")
        print(f"   95th Percentile: {result.p95_response_time:.3f}s")
        print(f"   99th Percentile: {result.p99_response_time:.3f}s")
        print(f"   Max Response Time: {result.max_response_time:.3f}s")
        
        if hasattr(result, 'system_metrics') and result.system_metrics:
            metrics = result.system_metrics
            print(f"   Avg CPU: {metrics.get('cpu_avg', 0):.1f}%")
            print(f"   Peak CPU: {metrics.get('cpu_max', 0):.1f}%")
            print(f"   Avg Memory: {metrics.get('memory_avg', 0):.1f}%")
            print(f"   Peak Memory: {metrics.get('memory_max', 0):.1f}%")
        
        if result.errors:
            unique_errors = list(set(result.errors))
            print(f"   Errors: {len(result.errors)} ({len(unique_errors)} unique)")
            for error in unique_errors[:3]:  # Show first 3 unique errors
                print(f"     - {error}")
    
    def _generate_final_report(self):
        """Generate final report"""
        print("\n" + "=" * 80)
        print("FINAL LOAD TEST REPORT")
        print("=" * 80)
        
        if not self.results:
            print("No test results available")
            return
        
        # Overall statistics
        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_failed = sum(r.failed_requests for r in self.results)
        overall_success_rate = (total_successful / total_requests * 100) if total_requests > 0 else 0
        
        print(f"Total Scenarios: {len(self.results)}")
        print(f"Total Requests: {total_requests}")
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"Total Failed: {total_failed}")
        
        # Performance summary
        all_response_times = []
        for result in self.results:
            all_response_times.extend(result.response_times)
        
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18]
            max_response_time = max(all_response_times)
            
            print(f"Overall Avg Response Time: {avg_response_time:.3f}s")
            print(f"Overall 95th Percentile: {p95_response_time:.3f}s")
            print(f"Overall Max Response Time: {max_response_time:.3f}s")
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = f"load_test_results_{timestamp}.json"
        self.config.save_results(results_file)
        
        print(f"\nDetailed results saved to: {results_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Voice Transcriber Load Test Runner")
    parser.add_argument("--scenario", help="Run specific scenario")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--list", action="store_true", help="List available scenarios")
    
    args = parser.parse_args()
    
    # Set up environment
    LoadTestEnvironment.setup_environment()
    
    try:
        # Create runner
        runner = LoadTestRunner(args.config)
        
        if args.list:
            print("Available scenarios:")
            for scenario_name in runner.config.list_scenarios():
                scenario = runner.config.get_scenario(scenario_name)
                print(f"  - {scenario_name}: {scenario.description}")
            return
        
        if args.scenario:
            runner.run_scenario(args.scenario)
        elif args.all:
            runner.run_all_scenarios()
        else:
            print("Please specify --scenario <name> or --all")
            print("Use --list to see available scenarios")
    
    except KeyboardInterrupt:
        print("\n⚠️ Load test interrupted by user")
    except Exception as e:
        print(f"❌ Load test failed: {e}")
    finally:
        LoadTestEnvironment.cleanup_environment()


if __name__ == '__main__':
    main()
