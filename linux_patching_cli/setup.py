#!/usr/bin/env python3
"""
Setup script for Linux Patching Automation CLI
"""

from setuptools import setup, find_packages
import os
import sys
from pathlib import Path

# Read version from version file
def get_version():
    version_file = Path(__file__).parent / 'version.txt'
    if version_file.exists():
        return version_file.read_text().strip()
    return '1.0.0'

# Read long description from README
def get_long_description():
    readme_file = Path(__file__).parent / 'README.md'
    if readme_file.exists():
        return readme_file.read_text(encoding='utf-8')
    return 'Linux Patching Automation CLI System'

# Read requirements from requirements.txt
def get_requirements():
    requirements_file = Path(__file__).parent / 'requirements.txt'
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            requirements = []
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Remove inline comments
                    req = line.split('#')[0].strip()
                    if req:
                        requirements.append(req)
            return requirements
    return []

# Filter requirements based on platform
def filter_requirements(requirements):
    filtered = []
    for req in requirements:
        # Skip platform-specific requirements if not on that platform
        if 'systemd-python' in req and sys.platform != 'linux':
            continue
        if 'dbus-python' in req and sys.platform != 'linux':
            continue
        if any(x in req for x in ['fcntl', 'termios', 'tty', 'pty', 'pwd', 'grp', 'spwd', 'crypt', 'syslog']) and sys.platform == 'win32':
            continue
        if 'readline' in req and sys.platform == 'win32':
            continue
        
        # Skip built-in modules that don't need installation
        builtin_modules = [
            'sqlite3', 'json', 'csv', 'xml.etree.ElementTree', 'os', 'sys',
            'subprocess', 'traceback', 'warnings', 'math', 'statistics', 
            'random', 'uuid', 'pickle', 'copyreg', 'tempfile', 'collections',
            'heapq', 'queue', 'itertools', 'functools', 'hashlib', 'base64',
            'urllib.parse', 'mimetypes', 'locale', 'glob', 'fnmatch', 'shlex',
            'string', 'textwrap', 'difflib', 'keyword', 'token', 'ast', 'dis',
            'inspect', 'types', 'typing', 'contextlib', 'weakref', 'copy',
            'pprint', 'reprlib', 'enum', 'decimal', 'fractions', 'secrets',
            'hmac', 'zlib', 'gzip', 'bz2', 'lzma', 'tarfile', 'zipfile',
            'shutil', 'signal', 'threading', 'platform', 'concurrent.futures',
            'multiprocessing', 'gc', 'resource', 're'
        ]
        
        if any(builtin in req for builtin in builtin_modules):
            continue
        
        filtered.append(req)
    
    return filtered

# Get requirements
requirements = get_requirements()
filtered_requirements = filter_requirements(requirements)

# Development requirements
dev_requirements = [
    'pytest>=6.2.5',
    'pytest-mock>=3.6.1',
    'pytest-cov>=2.12.1',
    'pytest-xdist>=2.3.0',
    'flake8>=3.9.0',
    'black>=21.0.0',
    'mypy>=0.910',
    'sphinx>=4.0.0',
    'sphinx-rtd-theme>=0.5.0'
]

# Optional requirements for advanced features
extras_require = {
    'dev': dev_requirements,
    'monitoring': [
        'prometheus-client>=0.11.0',
        'statsd>=3.3.0'
    ],
    'advanced': [
        'pandas>=1.3.0',
        'openpyxl>=3.0.7',
        'fabric>=2.6.0',
        'supervisor>=4.2.0',
        'sqlalchemy>=1.4.0',
        'alembic>=1.6.0'
    ],
    'performance': [
        'ujson>=4.0.0',
        'orjson>=3.6.0'
    ],
    'validation': [
        'marshmallow>=3.12.0',
        'cerberus>=1.3.2',
        'jsonschema>=3.2.0'
    ],
    'templates': [
        'jinja2>=3.0.0',
        'chevron>=0.13.0'
    ],
    'geo': [
        'timezonefinder>=6.0.0'
    ],
    'logging': [
        'loguru>=0.5.3',
        'structlog>=21.1.0'
    ],
    'snmp': [
        'easysnmp>=0.2.5'
    ],
    'security': [
        'keyring>=23.0.0'
    ],
    'all': [
        'pandas>=1.3.0',
        'openpyxl>=3.0.7',
        'fabric>=2.6.0',
        'prometheus-client>=0.11.0',
        'statsd>=3.3.0',
        'ujson>=4.0.0',
        'marshmallow>=3.12.0',
        'jinja2>=3.0.0',
        'timezonefinder>=6.0.0',
        'loguru>=0.5.3',
        'easysnmp>=0.2.5',
        'keyring>=23.0.0'
    ]
}

setup(
    name='linux-patching-automation',
    version=get_version(),
    description='Complete Linux Patching Automation CLI System',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    author='Linux Patching Team',
    author_email='patching@company.com',
    url='https://github.com/company/linux-patching-automation',
    
    # Package configuration
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'linux_patching_cli': [
            'data/*.csv',
            'config/*.py',
            'templates/*.html',
            'templates/*.txt',
            'scripts/*.sh',
            'docs/*.md'
        ]
    },
    
    # Requirements
    python_requires='>=3.6',
    install_requires=filtered_requirements,
    extras_require=extras_require,
    
    # Console scripts
    entry_points={
        'console_scripts': [
            'patch-manager=cli.patch_manager:main',
            'patching-cli=cli.patch_manager:main',
            'linux-patcher=cli.patch_manager:main'
        ]
    },
    
    # Classification
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Installation/Setup',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    
    # Keywords
    keywords='linux patching automation cli devops sysadmin',
    
    # Project URLs
    project_urls={
        'Documentation': 'https://github.com/company/linux-patching-automation/docs',
        'Source': 'https://github.com/company/linux-patching-automation',
        'Tracker': 'https://github.com/company/linux-patching-automation/issues',
        'Homepage': 'https://github.com/company/linux-patching-automation'
    },
    
    # Zip safe
    zip_safe=False,
    
    # Tests
    test_suite='tests',
    tests_require=dev_requirements,
    
    # Data files
    data_files=[
        ('share/doc/linux-patching-automation', ['README.md', 'LICENSE']),
        ('share/man/man1', ['docs/patch-manager.1']) if os.path.exists('docs/patch-manager.1') else [],
        ('etc/linux-patching-automation', ['config/settings.py.example']) if os.path.exists('config/settings.py.example') else [],
        ('usr/local/bin', ['scripts/install.sh']) if os.path.exists('scripts/install.sh') else []
    ],
    
    # Options
    options={
        'build_scripts': {
            'executable': '/usr/bin/python3'
        },
        'install': {
            'install_scripts': '/usr/local/bin'
        }
    },
    
    # Command classes for custom commands
    cmdclass={},
    
    # Distutils commands
    distclass=None,
    
    # Platform requirements
    platforms=['Linux', 'Unix'],
    
    # License
    license='MIT',
    
    # Maintainer
    maintainer='Linux Patching Team',
    maintainer_email='patching@company.com',
    
    # Download URL
    download_url='https://github.com/company/linux-patching-automation/releases',
    
    # Obsoletes
    obsoletes=[],
    
    # Provides
    provides=['linux_patching_automation'],
    
    # Requires
    requires=[],
    
    # Setup requires
    setup_requires=[
        'setuptools>=40.0.0',
        'wheel>=0.30.0'
    ],
    
    # Use 2to3
    use_2to3=False,
    
    # Convert 2to3 doctests
    convert_2to3_doctests=[],
    
    # Use 2to3 fixers
    use_2to3_fixers=[],
    
    # Eager resources
    eager_resources=[],
    
    # Dependency links
    dependency_links=[],
    
    # Namespace packages
    namespace_packages=[],
    
    # Scripts
    scripts=[],
    
    # Extension modules
    ext_modules=[],
    
    # Extension package
    ext_package=None,
    
    # Include dirs
    include_dirs=[],
    
    # Library dirs
    library_dirs=[],
    
    # Libraries
    libraries=[],
    
    # Headers
    headers=[],
    
    # SWIG opts
    swig_opts=[],
    
    # Language
    language=None
)

# Post-install message
print("""
Linux Patching Automation CLI has been installed successfully!

Next steps:
1. Run 'patch-manager --help' to see available commands
2. Configure your settings in config/settings.py
3. Set up your SSH keys for server access
4. Import your server inventory with 'patch-manager server import'
5. Start patching with 'patch-manager patch server --server <hostname>'

For documentation, visit: https://github.com/company/linux-patching-automation/docs
For support, contact: patching@company.com

Happy patching!
""")