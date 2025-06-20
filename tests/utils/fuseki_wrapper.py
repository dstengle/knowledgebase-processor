"""
Fuseki Test Wrapper for Apache Jena Fuseki integration testing.

This module provides a Python class to manage the lifecycle of a Fuseki server
for testing purposes, including starting, stopping, and health checking.
"""

import time
import subprocess
import requests
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import docker
from docker.errors import DockerException, NotFound, APIError

logger = logging.getLogger(__name__)


class FusekiTestWrapper:
    """
    Manages the lifecycle of an Apache Jena Fuseki server for testing.
    
    This wrapper supports both Docker and standalone modes for running Fuseki,
    with automatic health checking and cleanup capabilities.
    """
    
    def __init__(
        self,
        port: int = 3030,
        dataset: str = "test",
        mode: str = "docker",
        timeout: int = 30,
        admin_password: str = "admin"
    ):
        """
        Initialize the Fuseki test wrapper.
        
        Args:
            port: Port number for Fuseki server (default: 3030)
            dataset: Name of the dataset to create (default: "test")
            mode: Mode to run Fuseki ("docker" or "standalone")
            timeout: Timeout in seconds for server startup (default: 30)
            admin_password: Admin password for Fuseki (default: "admin")
        """
        self.port = port
        self.dataset = dataset
        self.mode = mode
        self.timeout = timeout
        self.admin_password = admin_password
        self.base_url = f"http://localhost:{port}"
        self.dataset_url = f"{self.base_url}/{dataset}"
        self.ping_url = f"{self.base_url}/$/ping"
        
        # Docker-specific attributes
        self.docker_client: Optional[docker.DockerClient] = None
        self.container = None
        
        # Standalone-specific attributes
        self.process: Optional[subprocess.Popen] = None
        
        if mode == "docker":
            try:
                self.docker_client = docker.from_env()
            except DockerException as e:
                raise RuntimeError(f"Failed to connect to Docker: {e}")
    
    def start(self) -> None:
        """
        Start the Fuseki server.
        
        Raises:
            RuntimeError: If the server fails to start or is unreachable
        """
        logger.info(f"Starting Fuseki server in {self.mode} mode on port {self.port}")
        
        if self.mode == "docker":
            self._start_docker()
        elif self.mode == "standalone":
            self._start_standalone()
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")
        
        # Wait for server to be ready
        if not self._wait_for_server():
            self.stop()  # Cleanup on failure
            raise RuntimeError(f"Fuseki server failed to start within {self.timeout} seconds")
        
        logger.info("Fuseki server started successfully")
    
    def stop(self) -> None:
        """Stop the Fuseki server and clean up resources."""
        logger.info("Stopping Fuseki server")
        
        try:
            if self.mode == "docker" and self.container:
                self._stop_docker()
            elif self.mode == "standalone" and self.process:
                self._stop_standalone()
        except Exception as e:
            logger.error(f"Error stopping Fuseki server: {e}")
        finally:
            self.container = None
            self.process = None
        
        logger.info("Fuseki server stopped")
    
    def is_running(self) -> bool:
        """
        Check if the Fuseki server is running and responsive.
        
        Returns:
            True if server is running and responsive, False otherwise
        """
        try:
            response = requests.get(self.ping_url, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def clear_data(self) -> None:
        """
        Clear all data from the test dataset.
        
        Raises:
            RuntimeError: If the server is not running or the operation fails
        """
        if not self.is_running():
            raise RuntimeError("Fuseki server is not running")
        
        try:
            # Clear the dataset using SPARQL UPDATE
            update_url = f"{self.dataset_url}/update"
            clear_query = "CLEAR ALL"
            
            response = requests.post(
                update_url,
                data={"update": clear_query},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()
            logger.info("Dataset cleared successfully")
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to clear dataset: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the Fuseki server.
        
        Returns:
            Dictionary containing server status information
        """
        status = {
            "running": self.is_running(),
            "mode": self.mode,
            "port": self.port,
            "dataset": self.dataset,
            "base_url": self.base_url,
            "dataset_url": self.dataset_url
        }
        
        if self.mode == "docker" and self.container:
            try:
                self.container.reload()
                status["container_status"] = self.container.status
                status["container_id"] = self.container.id[:12]
            except Exception:
                status["container_status"] = "unknown"
        
        return status
    
    def _start_docker(self) -> None:
        """Start Fuseki using Docker."""
        if not self.docker_client:
            raise RuntimeError("Docker client not initialized")
        
        # Check if container already exists
        container_name = f"fuseki-test-{self.port}"
        try:
            existing_container = self.docker_client.containers.get(container_name)
            logger.warning(f"Container {container_name} already exists, removing it")
            existing_container.remove(force=True)
        except NotFound:
            pass  # Container doesn't exist, which is what we want
        
        try:
            # Start new container
            self.container = self.docker_client.containers.run(
                "stain/jena-fuseki:latest",
                command=["--update", "--loc", "databases/test", f"/{self.dataset}"],
                ports={3030: self.port},
                environment={
                    "ADMIN_PASSWORD": self.admin_password,
                    "JVM_ARGS": "-Xmx1g"
                },
                name=container_name,
                detach=True,
                remove=True  # Auto-remove when stopped
            )
            logger.info(f"Started Docker container: {self.container.id[:12]}")
            
        except (DockerException, APIError) as e:
            raise RuntimeError(f"Failed to start Docker container: {e}")
    
    def _stop_docker(self) -> None:
        """Stop the Docker container."""
        if self.container:
            try:
                self.container.stop(timeout=10)
                logger.info("Docker container stopped")
            except Exception as e:
                logger.error(f"Error stopping Docker container: {e}")
                # Force kill if normal stop fails
                try:
                    self.container.kill()
                except Exception:
                    pass
    
    def _start_standalone(self) -> None:
        """Start Fuseki in standalone mode."""
        # This is a placeholder for standalone mode
        # In a real implementation, you would launch the Fuseki JAR file
        raise NotImplementedError("Standalone mode not implemented yet")
    
    def _stop_standalone(self) -> None:
        """Stop the standalone Fuseki process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
    
    def _wait_for_server(self) -> bool:
        """
        Wait for the Fuseki server to become available.
        
        Returns:
            True if server becomes available within timeout, False otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            if self.is_running():
                return True
            time.sleep(1)
        
        return False
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()