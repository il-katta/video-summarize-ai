from setuptools import setup, find_packages


def _is_valid_package(s: str) -> bool:
    if not s:
        return False
    if not s.strip():
        return False
    if s.startswith('#'):
        return False
    return True


def _sanitize_package(s: str) -> str:
    if s.startswith('git+'):
        pkg = s.split('#egg=')[1]
        s = f'{pkg} @ {s}'
    return s


with open('requirements.txt') as f:
    install_requires = [_sanitize_package(d) for d in f.read().splitlines() if _is_valid_package(d)]

setup(
    name='audio_summarize_ai',
    version='0.0.1',
    install_requires=install_requires,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'video_summary_simple = video_summary_simple.__main__:main',
            'video_summary_telegram_bot = video_summary_telegram_bot.__main__:main',
        ]
    }
)
