from setuptools import setup, find_packages

setup(
    name='ai-companion',
    version='0.1.0',
    description='An AI companion application with a web UI and interactive avatar.',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'flask',
        'flask-socketio',
        'numpy',
        'torch',
        'sqlite3',
        'sounddevice',
        'pyaudio',
        'requests',
        'pyttsx3',
        'speechrecognition',
        'opencv-python'
    ],
    entry_points={
        'console_scripts': [
            'ai-companion=main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)