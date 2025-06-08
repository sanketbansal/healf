#!/usr/bin/env python3
"""
Generate environment-specific Docker configuration files from templates.
Usage: python scripts/generate_docker_config.py <environment>
"""

import os
import sys
import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Add project root to path so we can import config
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_config

def get_template_variables(config, environment):
    """Extract template variables from config object"""
    
    # Basic configuration variables
    variables = {
        'environment': environment,
        'debug': str(config.DEBUG).lower(),
        'log_level': config.LOG_LEVEL,
        'api_v1_str': config.API_V1_STR,
        'project_name': config.PROJECT_NAME,
        'openai_api_key': getattr(config, 'OPENAI_API_KEY', ''),
        'llm_model': config.LLM_MODEL,
        'llm_temperature': config.LLM_TEMPERATURE,
        'llm_max_tokens': config.LLM_MAX_TOKENS,
        'max_questions': config.MAX_QUESTIONS,
        'min_age': config.MIN_AGE,
        'max_age': config.MAX_AGE,
    }
    
    # Docker-specific configuration
    if hasattr(config, 'DOCKER_CONFIG'):
        docker_config = config.DOCKER_CONFIG
        variables.update({
            'api_port': docker_config.get('api_port', 8000),
            'python_version': docker_config.get('python_version', '3.11'),
            'workers': docker_config.get('workers', 1),
            'memory_limit': docker_config.get('memory_limit', '512m'),
            'cpu_limit': docker_config.get('cpu_limit', '0.5'),
            'use_redis': docker_config.get('use_redis', True),
            'redis_version': docker_config.get('redis_version', '7'),
            'redis_password': docker_config.get('redis_password', ''),
            'mongo_version': docker_config.get('mongo_version', '7'),
            'mongo_password': docker_config.get('mongo_password', ''),
            'include_frontend': docker_config.get('include_frontend', False),
        })
    else:
        # Default values if DOCKER_CONFIG is not defined
        variables.update({
            'api_port': 8000,
            'python_version': '3.11',
            'workers': 1,
            'memory_limit': '512m',
            'cpu_limit': '0.5',
            'use_redis': False,
            'redis_version': '7',
            'redis_password': '',
            'mongo_version': '7',
            'mongo_password': '',
            'include_frontend': False,
        })
    
    return variables

def generate_docker_compose(environment, output_dir='.'):
    """Generate docker-compose.yml from unified template"""
    
    # Set environment variable for config loading
    os.environ['ENVIRONMENT'] = environment
    config = get_config()
    
    # Setup Jinja2 environment to look in templates directory
    template_dir = Path('templates')
    jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    # Load template
    template = jinja_env.get_template('docker-compose.template.yml')
    
    # Get template variables
    variables = get_template_variables(config, environment)
    
    # Render template
    rendered = template.render(**variables)
    
    # Write output
    output_file = Path(output_dir) / f'docker-compose.{environment}.yml'
    with open(output_file, 'w') as f:
        f.write(rendered)
    
    print(f"✅ Generated {output_file}")
    return output_file

def generate_dockerfile(environment, output_dir='.'):
    """Generate Dockerfile from unified template"""
    
    # Set environment variable for config loading
    os.environ['ENVIRONMENT'] = environment
    config = get_config()
    
    # Setup Jinja2 environment to look in templates directory
    template_dir = Path('templates')
    jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    # Load unified template
    template_file = 'Dockerfile.template'
    template_path = template_dir / template_file
    if not template_path.exists():
        print(f"⚠️  Template {template_path} not found, skipping Dockerfile generation")
        return None
    
    template = jinja_env.get_template(template_file)
    
    # Get template variables
    variables = get_template_variables(config, environment)
    
    # Render template
    rendered = template.render(**variables)
    
    # Write output
    output_file = Path(output_dir) / f'Dockerfile.{environment}'
    with open(output_file, 'w') as f:
        f.write(rendered)
    
    print(f"✅ Generated {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate Docker configuration files')
    parser.add_argument('environment', choices=['development', 'production', 'testing'],
                      help='Target environment')
    parser.add_argument('--output-dir', default='.', 
                      help='Output directory for generated files')
    parser.add_argument('--compose-only', action='store_true',
                      help='Generate only docker-compose file')
    parser.add_argument('--dockerfile-only', action='store_true',
                      help='Generate only Dockerfile')
    parser.add_argument('--clean', action='store_true',
                      help='Remove existing generated files before creating new ones')
    
    args = parser.parse_args()
    
    # Clean existing files if requested
    if args.clean:
        output_dir = Path(args.output_dir)
        compose_files = list(output_dir.glob('docker-compose.*.yml'))
        dockerfile_files = list(output_dir.glob('Dockerfile.*'))
        
        for file in compose_files + dockerfile_files:
            # Don't delete template files
            if not file.name.endswith('.template') and not file.name.endswith('.template.yml'):
                file.unlink()
                print(f"🗑️  Removed {file}")
    
    print(f"🚀 Generating Docker configuration for {args.environment} environment...")
    print(f"📁 Using templates from: templates/")
    
    generated_files = []
    
    if not args.dockerfile_only:
        compose_file = generate_docker_compose(args.environment, args.output_dir)
        if compose_file:
            generated_files.append(compose_file)
    
    if not args.compose_only:
        dockerfile = generate_dockerfile(args.environment, args.output_dir)
        if dockerfile:
            generated_files.append(dockerfile)
    
    print(f"\n✨ Generated {len(generated_files)} file(s) for {args.environment} environment:")
    for file in generated_files:
        print(f"   📄 {file}")
    
    print(f"\n🎯 To use the generated configuration:")
    print(f"   docker-compose -f docker-compose.{args.environment}.yml up --build")
    
    if args.environment == 'production':
        print(f"\n🔒 Production notes:")
        print(f"   - Multi-stage build for smaller image size")
        print(f"   - Non-root user for security")
        print(f"   - Multiple workers for performance")
    elif args.environment == 'development':
        print(f"\n🔧 Development notes:")
        print(f"   - Hot reload enabled")
        print(f"   - Volume mounting for live code changes")
        print(f"   - Debug tools included")

if __name__ == "__main__":
    main() 