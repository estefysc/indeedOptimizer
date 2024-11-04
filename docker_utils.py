import os

from logging_config import app_logger

logger = app_logger.getChild('DockerEnvironment')

class DockerEnvironment:
    """Utility class to detect if the current environment is running inside a Docker container.
    
    This class provides methods to check for Docker-specific indicators such as the presence
    of /.dockerenv file and Docker references in the cgroup configuration.
    """
    _is_docker = None

    @classmethod
    def is_running_in_docker(cls) -> bool:
        """Check if the current environment is running inside a Docker container.
        
        Returns:
            bool: True if running in Docker, False otherwise.
        """
        if cls._is_docker is None:
            cls._is_docker = cls._check_docker_environment()
        return cls._is_docker

    @staticmethod
    def _check_docker_environment() -> bool:
        """Perform actual Docker environment detection checks.
        
        Checks two indicators:
        1. Presence of /.dockerenv file
        2. Presence of 'docker' string in /proc/self/cgroup
        
        Returns:
            bool: True if either Docker indicator is found, False otherwise.
        """
        docker_env_exists = os.path.exists('/.dockerenv')
        docker_in_cgroup = False 

        try:
            with open('/proc/self/cgroup') as cgroup_file:
                # Read the entire content once
                cgroup_contents = cgroup_file.read()  

                # Check for 'docker' in the read content
                if 'docker' in cgroup_contents:
                    docker_in_cgroup = True

        except (IOError, FileNotFoundError):
            docker_in_cgroup = False
        
        is_docker = docker_env_exists or docker_in_cgroup
        logger.info(f"Running in Docker: {is_docker}")
        return is_docker