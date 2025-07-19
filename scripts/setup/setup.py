from setuptools import setup, find_packages

setup(
    name='ai2d_chat',
    version='0.4.0',
    description='AI Companion with Live2D Visual Avatar',
    author='AI Companion Team',
    author_email='contact@ai2d_chat.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    package_data={
        'web.static': [
            'dist/**/*.js',
            'dist/**/*.wasm',
            'dist/**/*.map', 
            'dist/**/*.json',
            'dist/**/*.md',
            'dist/**/*.txt',
            'dist/CubismSdkForWeb-5-r.4/**/*',
            'js/**/*.js',
            'css/**/*.css',
            '**/*.html'
        ],
        '': [
            '*.html', '*.css', '*.js', '*.json', '*.yaml', '*.yml', '*.md', '*.txt',
            'config_template.yaml', '.secrets.template'
        ]
    },
    install_requires=[
        'flask>=2.3.0',
        'flask-socketio>=5.3.0',
        'flask-cors>=4.0.0',
        'numpy>=1.21.0',
        'torch>=2.0.0',
        'torchaudio>=2.0.0',
        'transformers>=4.30.0',
        'sounddevice>=0.4.6',
        'soundfile>=0.12.1',
        'pydub>=0.25.1',
        'speechrecognition>=3.10.0',
        'pyaudio>=0.2.11',
        'requests>=2.31.0',
        'pyyaml>=6.0',
        'psutil>=5.9.0',
        'pillow>=10.0.0',
        'opencv-python>=4.8.0',
        'python-dotenv>=1.0.0',
        'tqdm>=4.64.0',
        'faster-whisper>=0.10.0',
        'llama-cpp-python>=0.2.0',
        'huggingface-hub>=0.16.0',
        'sqlalchemy>=2.0.0',
        # RAG and Vector Search Dependencies
        'sentence-transformers>=2.2.0',
        'chromadb>=0.4.0',
        'faiss-cpu>=1.7.0',  # Alternative: faiss-gpu for GPU support
        'numpy>=1.21.0',  # Already listed above but needed for vectors
        # Enhanced Logging and Monitoring
        'structlog>=23.0.0',
        'python-json-logger>=2.0.0',
        # Authentication and Security
        'flask-login>=0.6.0',
        'flask-session>=0.5.0',
        'werkzeug>=2.3.0',
        'bcrypt>=4.0.0',
        'pyjwt>=2.8.0',
        'cryptography>=41.0.0',
        # User Management and Sessions
        'redis>=4.5.0',  # Optional: for Redis session storage
        'python-multipart>=0.0.6',  # For file upload handling
    ],
    entry_points={
        'console_scripts': [
            'ai2d_chat=cli:main',
            'ai2d_chat-server=app:run_server',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
        'Topic :: Games/Entertainment',
        'Topic :: Communications :: Chat',
    ],
    python_requires='>=3.8',
)
